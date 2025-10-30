import pygame
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pygame.init()

# Window setup
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gamify")

font = pygame.font.Font(os.path.join(BASE_DIR, "cmu.ttf"), 50)
clock = pygame.time.Clock()
logo = pygame.image.load(os.path.join(BASE_DIR, "projectGamify.png")).convert_alpha()

# Colors
BG_COLOR = (15, 15, 20)
BTN_COLOR = (50, 50, 80)
HOVER_COLOR = (80, 80, 130)
TEXT_COLOR = (255, 255, 255)

# Button setup
button_width, button_height = 420, 110
buttons = {
    "Physics": pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT - 345, button_width, button_height),
    "Programming": pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT - 210, button_width, button_height)
}

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(BG_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if buttons["Physics"].collidepoint(mouse_pos):
                pygame.quit()
                os.chdir("physics")
                subprocess.run([sys.executable, "main.py"])
                sys.exit()
            elif buttons["Programming"].collidepoint(mouse_pos):
                pygame.quit()
                subprocess.run([sys.executable, "-m", "level_2_variables.main"])
                sys.exit()

    screen.blit(logo, ((WIDTH // 2) - logo.get_width() / 2, 10))
    for text, rect in buttons.items():
        hovered = rect.collidepoint(mouse_pos)
        color = HOVER_COLOR if hovered else BTN_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=16)
        text_surface = font.render(text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

