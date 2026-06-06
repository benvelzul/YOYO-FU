import pygame
import random 

pygame.init()
HEIGHT = 600
WIDTH = 800
SIZE = 20
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("YOYO-FU V1.0")
running = True

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

FPS = 60
clock = pygame.time.Clock()
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Controller detected: {joystick.get_name()}")

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

        # Integrate position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Keep inside bounds
        self.x = max(SIZE//2, min(self.x, WIDTH - SIZE//2))
        self.y = max(SIZE//2, min(self.y, HEIGHT - SIZE//2))

class Obstacles:
    def __init__(self):
        self.obstacles = []
    
    def add_obstacle(self, x, y, width, height):
        self.obstacles.append(pygame.Rect(x, y, width, height))

    def make_map(self, num_obs):
        for i in range(num_obs):
            w = random.randint(50, 150)
            h = random.randint(50, 150)
            x = random.randint(0, WIDTH - w)
            y = random.randint(0, HEIGHT - h)
            if x < WIDTH//2 - 100 and y < HEIGHT//2 - 100:
                continue  # Don't place obstacles too close to the center spawn area
            self.add_obstacle(x, y, w, h)
            
    def draw(self, surface):
        for obs in self.obstacles:
            pygame.draw.rect(surface, GREEN, obs)

class Yoyo:
    def __init__(self, owner):
        self.owner = owner
        self.x = owner.x
        self.y = owner.y
        self.speed = 5
        self.direction = (0, 0)
    
    def throw(self, target_x, target_y):
        dx = target_x - self.owner.x
        dy = target_y - self.owner.y
        length = (dx**2 + dy**2) ** 0.5
        if length > 0:
            self.direction = (dx / length, dy / length)

    def update(self, dt):
        self.x += self.direction[0] * self.speed * dt
        self.y += self.direction[1] * self.speed * dt
    
    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), 10)

player = Player("BEN")
yoyo = Yoyo(player)
obstacles = Obstacles()
obstacles.make_map(10)

DEADZONE = 0.15
while running:
    dt = clock.tick(FPS) / 1000.0

    # Keyboard fallback
    kb_x = 0
    kb_y = 0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        kb_y = -1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        kb_y = 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        kb_x = -1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        kb_x = 1

    # Read joystick input (left stick and D-pad/hats)
    joy_x = 0.0
    joy_y = 0.0
    hat_x = 0
    hat_y = 0
    if joystick is not None:
        try:
            joy_x = joystick.get_axis(0)
            joy_y = joystick.get_axis(1)
            if joystick.get_numhats() > 0:
                hat_x, hat_y = joystick.get_hat(0)
        except Exception:
            joy_x = 0.0
            joy_y = 0.0

    # Apply deadzone to analog stick
    if abs(joy_x) < DEADZONE:
        joy_x = 0.0
    if abs(joy_y) < DEADZONE:
        joy_y = 0.0

    # Preference: D-pad (hat) > analog stick > keyboard
    if hat_x != 0 or hat_y != 0:
        move_x = hat_x
        move_y = -hat_y
    elif joy_x != 0 or joy_y != 0:
        move_x = joy_x
        move_y = joy_y
    else:
        move_x = kb_x
        move_y = kb_y

    player.update(dt, move_x, move_y)

    screen.fill(BLACK)
    obstacles.draw(screen)
    pygame.draw.circle(screen, BLUE, (int(player.x), int(player.y)), SIZE // 2)
    pygame.display.flip()
