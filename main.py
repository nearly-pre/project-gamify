import pygame
import subprocess
import sys
import os
import math

baseDir = os.path.dirname(os.path.abspath(__file__))

pygame.init()

width, height = 1280, 720
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Gamify")

font = pygame.font.Font(os.path.join(baseDir, "cmu.ttf"), 50)
clock = pygame.time.Clock()
logo = pygame.image.load(os.path.join(baseDir, "projectGamify.png")).convert_alpha()

bgColor = (15, 15, 20)
btnColor = (50, 50, 80)
hoverColor = (80, 80, 130)
textColor = (255, 255, 255)

buttonWidth, buttonHeight = 420, 80
margin = 10
topMargin = 60

buttonLabels = ["Physics", "Programming", "Chemistry", "Mathematics", "Accounting", "Economics"]

logoHeight = logo.get_height()
availableHeight = height - (logoHeight + topMargin)
maxPerColumn = max(1, availableHeight // (buttonHeight + margin))

numColumns = math.ceil(len(buttonLabels) / maxPerColumn)
totalWidth = numColumns * buttonWidth + (numColumns - 1) * margin
startX = (width - totalWidth) // 2
startY = logoHeight + topMargin

buttons = {}
for i, label in enumerate(buttonLabels):
    col = i // maxPerColumn
    row = i % maxPerColumn
    x = startX + col * (buttonWidth + margin)
    y = startY + row * (buttonHeight + margin)
    buttons[label] = pygame.Rect(x, y, buttonWidth, buttonHeight)

running = True
while running:
    mousePos = pygame.mouse.get_pos()
    screen.fill(bgColor)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if buttons["Physics"].collidepoint(mousePos):
                pygame.quit()
                os.chdir("physics")
                subprocess.run([sys.executable, "main.py"])
                sys.exit()
            elif buttons["Programming"].collidepoint(mousePos):
                pygame.quit()
                subprocess.run([sys.executable, "-m", "level_2_variables.main"])
                sys.exit()

    screen.blit(logo, ((width // 2) - logo.get_width() / 2, 20))

    for text, rect in buttons.items():
        hovered = rect.collidepoint(mousePos)
        color = hoverColor if hovered else btnColor
        pygame.draw.rect(screen, color, rect, border_radius=16)
        textSurface = font.render(text, True, textColor)
        textRect = textSurface.get_rect(center=rect.center)
        screen.blit(textSurface, textRect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
