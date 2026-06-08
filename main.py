import os
import pygame
import random 

pygame.init()
HEIGHT = 600
WIDTH = 800
SIZE = 30
ASSET_DIR = os.path.join(os.path.dirname(__file__), "Images")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("YOYO-FU V1.0")
running = True

def load_image(name):
    path = os.path.join(ASSET_DIR, name)
    try:
        return pygame.image.load(path).convert_alpha()
    except pygame.error as exc:
        print(f"Unable to load image: {path}")
        raise exc

# Use only cactus_1 for all obstacle rendering.
cactus_image = load_image("Cactus_YF1.png")
# Animate the yoyo using the two frame images.
yoyo_frames = [
    pygame.transform.smoothscale(load_image("yoyo_YF0.png"), (SIZE//2, SIZE//2)),
    pygame.transform.smoothscale(load_image("yoyo_YF1.png"), (SIZE//2, SIZE//2)),
]
# Player sprite (scaled to SIZE)
player_image = pygame.transform.smoothscale(cactus_image, (SIZE, SIZE))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

FPS = 60
clock = pygame.time.Clock()
pygame.joystick.init()

class Player:
    def __init__(self, name):
        self.name = name
        self.kills = 0
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.max_speed = 250
        # Higher values make the player reach the target velocity faster (sharper turns)
        self.turn_responsiveness = 12.0

    def update(self, dt, move_x, move_y):
        # Compute desired velocity based on input direction and magnitude
        mag = (move_x * move_x + move_y * move_y) ** 0.5
        if mag > 0:
            nx = move_x / mag
            ny = move_y / mag
            # allow analog magnitude to scale target speed (for controllers)
            target_vx = nx * self.max_speed * min(1.0, mag)
            target_vy = ny * self.max_speed * min(1.0, mag)

            # Lerp velocity toward target to control turning sharpness
            t = min(1.0, self.turn_responsiveness * dt)
            self.vx += (target_vx - self.vx) * t
            self.vy += (target_vy - self.vy) * t

        else:
            # No input: stop immediately (no glide)
            self.vx = 0.0
            self.vy = 0.0

        # Clamp velocity
        self.vx = max(-self.max_speed, min(self.vx, self.max_speed))
        self.vy = max(-self.max_speed, min(self.vy, self.max_speed))

        # Integrate position axis-by-axis for better collision response
        self.x += self.vx * dt
        if obstacles.check_collision(self):
            self.x -= self.vx * dt
            self.vx = 0.0

        self.y += self.vy * dt
        if obstacles.check_collision(self):
            self.y -= self.vy * dt
            self.vy = 0.0

        # Keep inside bounds
        self.x = max(SIZE//2, min(self.x, WIDTH - SIZE//2))
        self.y = max(SIZE//2, min(self.y, HEIGHT - SIZE//2))

class Obstacles:
    def __init__(self):
        self.obstacles = []
    
    def add_obstacle(self, x, y, width, height):
        self.obstacles.append(pygame.Rect(x, y, width, height))

    def rect_circle_overlap(self, rect, center, radius):
        cx, cy = center
        # Find closest point on rect to circle center
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx * dx + dy * dy) <= (radius * radius)

    def make_map(self, num_obs):
        spawn_cx = WIDTH // 2
        spawn_cy = HEIGHT // 2
        spawn_radius = 120  # radius around center where obstacles won't spawn

        placed = 0
        attempts = 0
        max_attempts = num_obs * 10
        while placed < num_obs and attempts < max_attempts:
            attempts += 1
            w = random.randint(50, 150)
            h = random.randint(50, 150)
            x = random.randint(0, WIDTH - w)
            y = random.randint(0, HEIGHT - h)
            candidate = pygame.Rect(x, y, w, h)

            # Skip obstacles that overlap the spawn circle
            if self.rect_circle_overlap(candidate, (spawn_cx, spawn_cy), spawn_radius):
                continue

            # Otherwise place it
            self.add_obstacle(x, y, w, h)
            placed += 1
            
    def check_collision(self, player):
        player_rect = pygame.Rect(int(player.x - SIZE//2), int(player.y - SIZE//2), SIZE, SIZE)
        for obs in self.obstacles:
            if player_rect.colliderect(obs):
                return True
        return False
    
    def check_yoyo_collision(self, yoyo):
        yoyo_rect = pygame.Rect(int(yoyo.x - 10), int(yoyo.y - 10), 20, 20)
        for obs in self.obstacles:
            if yoyo_rect.colliderect(obs):
                return True
        return False
    
    def draw(self, surface):
        for obs in self.obstacles:
            pygame.draw.rect(surface, GREEN, obs)

class Yoyo:
    def __init__(self, owner):
        self.owner = owner
        self.x = owner.x
        self.y = owner.y
        self.speed = 420
        self.return_speed = 520
        self.direction = (0.0, 0.0)
        self.state = "attached"
        self.max_range = 280
        self.travel_distance = 0.0
        self.animation_timer = 0.0
        self.animation_frame = 0
        self.animation_speed = 0.15

    def attach(self):
        self.state = "attached"
        self.direction = (0.0, 0.0)
        self.travel_distance = 0.0
        self.x = self.owner.x
        self.y = self.owner.y

    def recall(self):
        if self.state == "outbound":
            self.state = "recalled"

    def throw(self, direction_x, direction_y):
        if self.state != "attached":
            return
        mag = (direction_x ** 2 + direction_y ** 2) ** 0.5
        if mag > 0.0:
            self.direction = (direction_x / mag, direction_y / mag)
            self.state = "outbound"
            self.travel_distance = 0.0
            self.x = self.owner.x
            self.y = self.owner.y

    def update(self, dt):
        if self.state == "attached":
            self.x = self.owner.x
            self.y = self.owner.y
            return

        if self.state == "outbound":
            prev_x = self.x
            prev_y = self.y
            vel_x = self.direction[0] * self.speed * dt
            vel_y = self.direction[1] * self.speed * dt
            self.x += vel_x
            self.y += vel_y
            self.travel_distance += (vel_x ** 2 + vel_y ** 2) ** 0.5

            # Bounce off the screen bounds.
            radius = 10
            bounced = False
            if self.x < radius:
                self.x = radius
                self.direction = (-self.direction[0], self.direction[1])
                bounced = True
            elif self.x > WIDTH - radius:
                self.x = WIDTH - radius
                self.direction = (-self.direction[0], self.direction[1])
                bounced = True
            if self.y < radius:
                self.y = radius
                self.direction = (self.direction[0], -self.direction[1])
                bounced = True
            elif self.y > HEIGHT - radius:
                self.y = HEIGHT - radius
                self.direction = (self.direction[0], -self.direction[1])
                bounced = True

            # Bounce from obstacles if the yoyo hits them.
            if obstacles.check_yoyo_collision(self):
                # Restore previous position and reflect on the collision axis.
                self.x = prev_x
                self.y = prev_y
                if abs(vel_x) > abs(vel_y):
                    self.direction = (-self.direction[0], self.direction[1])
                else:
                    self.direction = (self.direction[0], -self.direction[1])
                bounced = True
                self.x += self.direction[0] * self.speed * dt
                self.y += self.direction[1] * self.speed * dt

            if self.travel_distance >= self.max_range:
                self.state = "returning"

        if self.state == "returning" or self.state == "recalled":
            dx = self.owner.x - self.x
            dy = self.owner.y - self.y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= 8.0:
                self.attach()
                return
            direction_x = dx / dist
            direction_y = dy / dist
            move_x = direction_x * self.return_speed * dt
            move_y = direction_y * self.return_speed * dt
            if (move_x ** 2 + move_y ** 2) ** 0.5 >= dist:
                self.attach()
            else:
                self.x += move_x
                self.y += move_y

        self.x = max(0, min(self.x, WIDTH))
        self.y = max(0, min(self.y, HEIGHT))

        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer -= self.animation_speed
            self.animation_frame = (self.animation_frame + 1) % len(yoyo_frames)

    def draw(self, surface):
        if self.state != "attached":
            pygame.draw.line(surface, WHITE, (int(self.owner.x), int(self.owner.y)), (int(self.x), int(self.y)), 2)
        frame = yoyo_frames[self.animation_frame]
        frame_rect = frame.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(frame, frame_rect)

class Controls:
    DEADZONE = 0.15
    PREVIEW_THRESHOLD = 0.18
    BUTTON_NAMES = {
        0: "A",
        1: "B",
        2: "X",
        3: "Y",
        4: "MINUS",
        5: "Home",
        6: "PLUS",
        7: "LeftStickPress",
        8: "RightStickPress",
        9: "LeftBumper",
        10: "RightBumper",
        11: "ArrowUp",
        12: "ArrowDown",
        13: "ArrowLeft",
        14: "ArrowRight",
        15: "ScreenShot",
    }

    def __init__(self):
        self.joystick = None
        self.fire_pressed = False
        self.fire_released = False
        self.fire_held = False
        self.fire_hold_time = 0.0
        self.aim_direction = (1.0, 0.0)
        self.last_key = None
        self.last_button = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller detected: {self.joystick.get_name()}")

    def _deadzone(self, value):
        return value if abs(value) >= self.DEADZONE else 0.0

    def start_fire(self):
        if not self.fire_held:
            self.fire_pressed = True
            self.fire_held = True
            self.fire_hold_time = 0.0
        
    def process_events(self):
        self.fire_pressed = False
        self.fire_released = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                self.last_key = event.key
                print(f"Key pressed: {pygame.key.name(event.key)} ({event.key})")
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.start_fire()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and self.fire_held:
                    self.fire_released = True
                    self.fire_held = False
                if event.key == pygame.K_SPACE and yoyo.state == "outbound":
                    yoyo.recall()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.start_fire()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.fire_held:
                    self.fire_released = True
                    self.fire_held = False
                if event.button == 1 and yoyo.state == "outbound":
                    yoyo.recall()
            elif event.type == pygame.JOYBUTTONDOWN:
                self.last_button = event.button
                button_name = self.BUTTON_NAMES.get(event.button, f"Button {event.button}")
                print(f"Joystick {event.joy} button pressed: {event.button} ({button_name})")
                if event.button == 0:
                    self.start_fire()
            elif event.type == pygame.JOYBUTTONUP:
                if event.button == 0 and self.fire_held:
                    self.fire_released = True
                    self.fire_held = False
                if event.button == 0 and yoyo.state == "outbound":
                    yoyo.recall()
            elif event.type == pygame.JOYHATMOTION:
                print(f"Joystick {event.joy} hat {event.hat} moved: {event.value}")
        return True

    def update(self, dt):
        if self.fire_held:
            self.fire_hold_time += dt

    def aim_vector(self, owner_x, owner_y):
        if self.joystick is not None:
            try:
                aim_x = self.joystick.get_axis(0)
                aim_y = self.joystick.get_axis(1)
                aim_x = self._deadzone(aim_x)
                aim_y = self._deadzone(aim_y)
                if aim_x != 0.0 or aim_y != 0.0:
                    mag = (aim_x * aim_x + aim_y * aim_y) ** 0.5
                    self.aim_direction = (aim_x / mag, aim_y / mag)
                    return self.aim_direction
            except Exception:
                pass

        keys = pygame.key.get_pressed()
        aim_x = 0.0
        aim_y = 0.0
        if keys[pygame.K_w]:
            aim_y -= 1.0
        if keys[pygame.K_s]:
            aim_y += 1.0
        if keys[pygame.K_a]:
            aim_x -= 1.0
        if keys[pygame.K_d]:
            aim_x += 1.0

        if aim_x != 0.0 or aim_y != 0.0:
            mag = (aim_x * aim_x + aim_y * aim_y) ** 0.5
            self.aim_direction = (aim_x / mag, aim_y / mag)

        return self.aim_direction

    def aim_point(self, owner_x, owner_y, distance):
        dx, dy = self.aim_vector(owner_x, owner_y)
        return owner_x + dx * distance, owner_y + dy * distance

    def wants_preview(self):
        return self.fire_held and self.fire_hold_time >= self.PREVIEW_THRESHOLD

    def get_move(self):
        kb_x = 0.0
        kb_y = 0.0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            kb_y -= 1.0
        if keys[pygame.K_s]:
            kb_y += 1.0
        if keys[pygame.K_a]:
            kb_x -= 1.0
        if keys[pygame.K_d]:
            kb_x += 1.0

        joy_x = 0.0
        joy_y = 0.0
        hat_x = 0
        hat_y = 0
        if self.joystick is not None:
            try:
                joy_x = self.joystick.get_axis(0)
                joy_y = self.joystick.get_axis(1)
                if self.joystick.get_numhats() > 0:
                    hat_x, hat_y = self.joystick.get_hat(0)
            except Exception:
                joy_x = 0.0
                joy_y = 0.0

        joy_x = self._deadzone(joy_x)
        joy_y = self._deadzone(joy_y)

        if hat_x != 0 or hat_y != 0:
            return float(hat_x), float(-hat_y)
        if joy_x != 0.0 or joy_y != 0.0:
            return float(joy_x), float(joy_y)
        return kb_x, kb_y

player = Player("BEN")
controls = Controls()
yoyo = Yoyo(player)
obstacles = Obstacles()
obstacles.make_map(20)

while running:
    dt = clock.tick(FPS) / 1000.0

    running = controls.process_events()
    if not running:
        break

    controls.update(dt)

    # When aiming (holding the fire button) the player should not be able to move.
    # Throw the yoyo when the fire is released, not immediately when held.
    if controls.fire_released and yoyo.state == "attached":
        aim_x, aim_y = controls.aim_vector(player.x, player.y)
        yoyo.throw(aim_x, aim_y)
    else:
        if controls.fire_held:
            # Player is aiming: block movement
            move_x, move_y = 0.0, 0.0
        else:
            move_x, move_y = controls.get_move()
        player.update(dt, move_x, move_y)

    yoyo.update(dt)

    screen.fill(BLACK)
    obstacles.draw(screen)
    # Draw player as cactus sprite
    player_rect = player_image.get_rect(center=(int(player.x), int(player.y)))
    screen.blit(player_image, player_rect)

    if controls.wants_preview() and yoyo.state == "attached":
        preview_x, preview_y = controls.aim_point(player.x, player.y, 40)
        pygame.draw.circle(screen, (255, 255, 0), (int(preview_x), int(preview_y)), 14, 3)

    yoyo.draw(screen)
    pygame.display.flip()
