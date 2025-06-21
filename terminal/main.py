import pygame
from sys import exit
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

WIDTH = 1280
HEIGHT = 720
TAB = "   "
TERMINAL_PADDING = (30, 70)
TERMINAL_SIZE = (640, 380)

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("python teacher")
clock = pygame.time.Clock()

terminal = pygame.Surface(TERMINAL_SIZE)
terminal.fill((48, 44, 44))
terminalPos = (10, 10)

runButton = pygame.Surface((31, 31))
runButton.fill((98, 109, 18))

font = pygame.font.Font("./JetBrainsMono-Regular.ttf", 25)
inputTextSurfaces = [0]
inputTexts = [""]
inputIndex = 0
backspaceSleep = 0

running = True

def lineHighlight(text):
    colors = {
        Token.Keyword: (186, 218, 85),
        Token.Operator: (97, 214, 214),
        Token.Punctuation: (170, 170, 170),
        Token.Name: (220, 224, 230),
        Token.Name.Function: (97, 175, 239),
        Token.Name.Class: (229, 192, 123),
        Token.Name.Builtin: (86, 182, 194),
        Token.Name.Decorator: (86, 182, 194),
        Token.String: (206, 145, 120),
        Token.String.Doc: (106, 153, 85),
        Token.Number: (180, 145, 230),
        Token.Name.Constant: (206, 145, 120),
        Token.Comment: (98, 114, 130),
        Token.Text: (220, 224, 230),
    }

    surfaces = []
    x = 0
    for tokenType, tokenValue in lex(text, PythonLexer()):
        if tokenValue == '\n':
            continue
        
        if tokenValue.isspace():
            tokenValue = ' ' * len(tokenValue)

        color = colors.get(tokenType, (220, 224, 230))
        tokenSurface = font.render(tokenValue, True, color)
        surfaces.append((tokenSurface, x))
        x += tokenSurface.get_width()

    return surfaces

while running:
    screen.fill((67, 153, 101))
    terminal.fill((48, 44, 44))
    # runButton.fill((98, 172, 58))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                continue
            if event.key == pygame.K_RETURN:
                prevIndex = inputIndex
                inputIndex += 1
                inputTexts.append("")
                inputTextSurfaces.append(0)

                if inputTexts[prevIndex]:
                    for char in inputTexts[prevIndex]:
                        if char != " ":
                            break
                        else:
                            inputTexts[inputIndex] += " "
                    if inputTexts[prevIndex][-1] == ":":
                        inputTexts[inputIndex] += TAB
                        
                continue
            if event.key == pygame.K_TAB:
                inputTexts[inputIndex] += TAB
                continue
            else:
                inputTexts[inputIndex] += event.unicode
            inputTextSurfaces[inputIndex] = lineHighlight(inputTexts[inputIndex])
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mousePos = pygame.mouse.get_pos()
            runButtonRect = pygame.Rect(60, 60, 31, 31)

            if runButtonRect.collidepoint(mousePos):
                print("Run button clicked!")
                continue            
            
    keys = pygame.key.get_pressed()
    if keys[pygame.K_BACKSPACE] and keys[pygame.K_LCTRL]:
        if not (backspaceSleep % 5):
            if inputTexts[inputIndex].isspace():
                lastDelim = 0
            else:
                lastDelim = inputTexts[inputIndex].rfind(' ')
            inputTexts[inputIndex] = inputTexts[inputIndex][:(0 if lastDelim == -1 else lastDelim)]
            inputTextSurfaces[inputIndex] = lineHighlight(inputTexts[inputIndex])
        backspaceSleep += 1

    elif keys[pygame.K_BACKSPACE]:
        if not (backspaceSleep % 5):
            inputTexts[inputIndex] = inputTexts[inputIndex][:-1]
            inputTextSurfaces[inputIndex] = lineHighlight(inputTexts[inputIndex])
        backspaceSleep += 1

    for index, surfaces in enumerate(inputTextSurfaces):
        if surfaces:
            for surface, x in surfaces:
                terminal.blit(surface, (TERMINAL_PADDING[0] + x, index * 45 + TERMINAL_PADDING[1]))

    if inputTexts[inputIndex]:
        cursorOffset = font.size(inputTexts[inputIndex])[0] + TERMINAL_PADDING[0] + 50
    else:
        cursorOffset = TERMINAL_PADDING[0] + 50

    pygame.draw.rect(terminal, (58, 54, 54), (0, 0, TERMINAL_SIZE[0], 50))
    terminal.blit(runButton, terminalPos)
    pygame.draw.polygon(runButton, (255, 255, 255), [(8, 6), (8, 24), (23, 15)])
    screen.blit(terminal, (50, 50))
    cursorStartY = inputIndex * 45 + TERMINAL_PADDING[1] + 50
    cursorEndY = cursorStartY + font.get_height()
    cursor = pygame.draw.line(screen, (255, 255, 255), (cursorOffset, cursorStartY), (cursorOffset, cursorEndY), width=2)
    pygame.display.flip()
    clock.tick(60)
