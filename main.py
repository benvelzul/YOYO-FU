
    raise SystemExit

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("YOYO-FU V1.0")
running = True

#Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

class Player:
    def __init__(self, name):
        self.name = name
        self.kills = 0
        self.x = 200
        self.y = 150
        self.alive = True

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

player = Player("BEN")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                player.move(0, -10)
            elif event.key == pygame.K_s:
                player.move(0, 10)
            elif event.key == pygame.K_a:
                player.move(-10, 0)
            elif event.key == pygame.K_d:
                player.move(10, 0)

    screen.fill(BLACK)
    pygame.draw.circle(screen, BLUE, (player.x, player.y), 50)
    pygame.display.flip()
