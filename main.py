import math
import os
import pygame
import random 

pygame.init()
HEIGHT = 600
WIDTH = 800
SIZE = 40
PLAYER_HITBOX_PADDING = 8
PLAYER_HITBOX_SIZE = SIZE - PLAYER_HITBOX_PADDING
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
player_images = [pygame.transform.smoothscale(load_image("Cactus_YF1.png"), (SIZE, SIZE)),
                 pygame.transform.smoothscale(load_image("Cactus_YF0.png"), (SIZE, SIZE)),
                 pygame.transform.smoothscale(load_image("Cactus_YF2.png"), (SIZE, SIZE)),
                 pygame.transform.smoothscale(load_image("Cactus_YF3.png"), (SIZE, SIZE)),]
# Animate the yoyo using the two frame images.
yoyo_frames = [
    pygame.transform.smoothscale(load_image("yoyo_YF0.png"), (int(SIZE*0.4), int(SIZE*0.4))),
    pygame.transform.smoothscale(load_image("yoyo_YF1.png"), (int(SIZE*0.4), int(SIZE*0.4))),
]


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
        player_rect = pygame.Rect(
            int(player.x - PLAYER_HITBOX_SIZE//2),
            int(player.y - PLAYER_HITBOX_SIZE//2),
            PLAYER_HITBOX_SIZE,
            PLAYER_HITBOX_SIZE,
        )
        for obs in self.obstacles:
            if player_rect.colliderect(obs):
                return True
        return False
    
    def check_yoyo_collision(self, yoyo):
        yoyo_rect = yoyo.yoyo_rect()
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
        self.radius = 10
        self.base_speed = 420.0
        self.base_return_speed = 520.0
        self.speed = self.base_speed
        self.return_speed = self.base_return_speed
        self.direction = (0.0, 0.0)
        self.state = "attached"
        self.max_range = 280
        self.travel_distance = 0.0
        self.bounce_count = 0
        self.max_bounces = 8
        self.bounce_friction = 0.78
        self.min_speed = 220.0
        self.min_return_speed = 260.0
        self.animation_timer = 0.0
        self.animation_frame = 0
        self.animation_speed = 0.15

    def yoyo_rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    def _apply_bounce_friction(self):
        self.bounce_count += 1
        self.speed = max(self.min_speed, self.speed * self.bounce_friction)
        self.return_speed = max(self.min_return_speed, self.return_speed * self.bounce_friction)

    def break_string(self):
        self.state = "broken"
        self.direction = (0.0, 0.0)

    def _apply_motion(self, vel_x, vel_y, speed, dt):
        prev_x = self.x
        prev_y = self.y
        self.x += vel_x
        self.y += vel_y
        bounced = False

        # Bounce off screen bounds first
        if self.x < self.radius:
            self.x = self.radius
            self.direction = (-self.direction[0], self.direction[1])
            bounced = True
        elif self.x > WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.direction = (-self.direction[0], self.direction[1])
            bounced = True
        if self.y < self.radius:
            self.y = self.radius
            self.direction = (self.direction[0], -self.direction[1])
            bounced = True
        elif self.y > HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            self.direction = (self.direction[0], -self.direction[1])
            bounced = True

        if obstacles.check_yoyo_collision(self):
            self.x = prev_x
            self.y = prev_y
            x_collided = False
            y_collided = False

            self.x = prev_x + vel_x
            self.y = prev_y
            if obstacles.check_yoyo_collision(self):
                self.x = prev_x
                self.direction = (-self.direction[0], self.direction[1])
                x_collided = True

            self.x = prev_x
            self.y = prev_y + vel_y
            if obstacles.check_yoyo_collision(self):
                self.y = prev_y
                self.direction = (self.direction[0], -self.direction[1])
                y_collided = True

            if not (x_collided or y_collided):
                self.direction = (-self.direction[0], -self.direction[1])

            self.x = prev_x + self.direction[0] * speed * dt
            self.y = prev_y + self.direction[1] * speed * dt
            bounced = True

            self.x = max(self.radius, min(self.x, WIDTH - self.radius))
            self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

        if bounced:
            self._apply_bounce_friction()

        return bounced

    def attach(self):
        self.state = "attached"
        self.direction = (0.0, 0.0)
        self.travel_distance = 0.0
        self.x = self.owner.x
        self.y = self.owner.y
        self.speed = self.base_speed
        self.return_speed = self.base_return_speed
        self.bounce_count = 0
        self.break_timer = 0.0

    def recall(self):
        if self.state == "outbound":
            self.state = "recalled"
            dx = self.owner.x - self.x
            dy = self.owner.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0.0:
                self.direction = (dx / dist, dy / dist)

    def _start_return(self):
        self.state = "returning"
        dx = self.owner.x - self.x
        dy = self.owner.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0.0:
            self.direction = (dx / dist, dy / dist)

    def throw(self, direction_x, direction_y):
        if self.state != "attached":
            return
        mag = (direction_x ** 2 + direction_y ** 2) ** 0.5
        if mag > 0.0:
            self.direction = (direction_x / mag, direction_y / mag)
            self.state = "outbound"
            self.travel_distance = 0.0
            self.bounce_count = 0
            self.speed = self.base_speed
            self.return_speed = self.base_return_speed
            self.x = self.owner.x
            self.y = self.owner.y
    def check_collision_with_owner(self):
        if self.state in ("broken"):
            if math.hypot(self.owner.x - self.x, self.owner.y - self.y) <= self.radius + SIZE//2:
                self.attach() 
                return True
        return False       
    
    def update(self, dt):
        if self.state == "attached":
            self.x = self.owner.x
            self.y = self.owner.y
            return

        if self.state == "broken":
            checked = self.check_collision_with_owner()
            if checked:
                return
            else:
                return
            

        if self.state == "outbound":
            vel_x = self.direction[0] * self.speed * dt
            vel_y = self.direction[1] * self.speed * dt
            self.travel_distance += math.hypot(vel_x, vel_y)
            self._apply_motion(vel_x, vel_y, self.speed, dt)

            if self.travel_distance >= self.max_range:
                self._start_return()

        if self.state == "returning" or self.state == "recalled":
            if self.state == "recalled":
                self.state = "returning"
            dx = self.owner.x - self.x
            dy = self.owner.y - self.y
            dist = math.hypot(dx, dy)
            if dist <= 8.0:
                self.attach()
                return

            self.direction = (dx / dist, dy / dist)

            vel_x = self.direction[0] * self.return_speed * dt
            vel_y = self.direction[1] * self.return_speed * dt
            move_len = math.hypot(vel_x, vel_y)

            if move_len >= dist:
                self.attach()
            else:
                self._apply_motion(vel_x, vel_y, self.return_speed, dt)
                if self.bounce_count >= self.max_bounces:
                    self.break_string()
                    return

        self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer -= self.animation_speed
            self.animation_frame = (self.animation_frame + 1) % len(yoyo_frames)

    def draw(self, surface):
        if self.state not in ("attached", "broken"):
            pygame.draw.line(surface, WHITE, (int(self.owner.x), int(self.owner.y)), (int(self.x), int(self.y)), 2)
        frame = yoyo_frames[self.animation_frame]
        frame_rect = frame.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(frame, frame_rect)

class Controls:
    DEADZONE = 0.17
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

    if controls.wants_preview() and yoyo.state == "attached":
        preview_x, preview_y = controls.aim_point(player.x, player.y, 40)
        pygame.draw.circle(screen, (255, 255, 0), (int(preview_x), int(preview_y)), 14, 3)
        # Draw player as cactus sprite
        player_rect = player_images[1].get_rect(center=(int(player.x), int(player.y)))
        screen.blit(player_images[1], player_rect)
    else:
        # Draw player as cactus sprite
        player_rect = player_images[0].get_rect(center=(int(player.x), int(player.y)))
        screen.blit(player_images[0], player_rect)

    yoyo.draw(screen)
    pygame.display.flip()
