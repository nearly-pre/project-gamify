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
terminalPosition = (10, 10)

runButton = pygame.Surface((31, 31))
runButton.fill((98, 109, 18))

font = pygame.font.Font("./JetBrainsMono-Regular.ttf", 25)
lineSurfaces = [0]
codeLines = [""]
currentLineIndex = 0
backspaceDelayCounter = 0

running = True

def codeLineHighlight(text):
    """Function that highlights codes in real-time, as the user types. It's not important to understand
    what the following code does. If you're really curious, search up lexing."""

    # all the token colors. Chat-gpted, obviously. 
    tokenColors = {
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

        color = tokenColors.get(tokenType, (220, 224, 230))
        tokenSurface = font.render(tokenValue, True, color)
        surfaces.append((tokenSurface, x))
        x += tokenSurface.get_width()

    return surfaces

while running:
    screen.fill((67, 153, 101))
    terminal.fill((48, 44, 44))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                previousLineIndex = currentLineIndex
                currentLineIndex += 1
                codeLines.append("")
                lineSurfaces.append(0)

                # auto-formatting
                if codeLines[previousLineIndex]:
                    for char in codeLines[previousLineIndex]:
                        if char != " ":
                            break
                        else:
                            codeLines[currentLineIndex] += " "
                    if codeLines[previousLineIndex][-1] == ":":
                        codeLines[currentLineIndex] += TAB
                continue
            elif event.key == pygame.K_TAB:
                codeLines[currentLineIndex] += TAB
                continue
            else:
                codeLines[currentLineIndex] += event.unicode # event.unicode helps identify keyboard shortcuts
                
            lineSurfaces[currentLineIndex] = codeLineHighlight(codeLines[currentLineIndex])
            
        # if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        #     mousePos = pygame.mouse.get_pos()
        #     runButtonRect = pygame.Rect(60, 60, 31, 31)

        #     if runButtonRect.collidepoint(mousePos):
        #         print("Run button clicked!")
        #         continue            

    # The backspace check is handled separately from the main event loop because KEYDOWN events are
    # only triggered once when a key is pressed. Holding a key down has no effect, the user would need
    # to repeatedly press the key to get the desired "holding down" effect. So checking for backspace
    # inside the event loop would only register a single press. We don't want that, so we keep it
    # separate from the event loop and bring it down to the actual game loop, which allows the user
    # to "hold" a key.
    
    pressedKeys = pygame.key.get_pressed()

    # backspace mechanism
    if pressedKeys[pygame.K_BACKSPACE]:
        if not (backspaceDelayCounter % 5):
            if pressedKeys[pygame.K_LCTRL]:
                # if backspace + ctrl are pressed simultaneously, delete whole words
                if codeLines[currentLineIndex].isspace():
                    lastDelimiterIndex = 0
                else:
                    lastDelimiterIndex = codeLines[currentLineIndex].rfind(' ')
                codeLines[currentLineIndex] = codeLines[currentLineIndex][:(0 if lastDelimiterIndex == -1 else lastDelimiterIndex)]
                lineSurfaces[currentLineIndex] = codeLineHighlight(codeLines[currentLineIndex])
                
            else:
                # if only backspace is pressed, delete single characters
                if not (backspaceDelayCounter % 5):
                    codeLines[currentLineIndex] = codeLines[currentLineIndex][:-1]
                    lineSurfaces[currentLineIndex] = codeLineHighlight(codeLines[currentLineIndex])

            if codeLines[currentLineIndex] == "" and currentLineIndex != 0:
                currentLineIndex -= 1
                codeLines.pop()
                lineSurfaces.pop()
                    
        backspaceDelayCounter += 1

    # text blitting handled here
    for lineIndex, surfaces in enumerate(lineSurfaces):
        if surfaces:
            for surface, x in surfaces:
                terminal.blit(surface, (TERMINAL_PADDING[0] + x, lineIndex * 45 + TERMINAL_PADDING[1]))

    # cursor
    if codeLines[currentLineIndex]:
        cursorXOffset = font.size(codeLines[currentLineIndex])[0] + TERMINAL_PADDING[0] + 50
    else:
        cursorXOffset = TERMINAL_PADDING[0] + 50

    
    pygame.draw.rect(terminal, (58, 54, 54), (0, 0, TERMINAL_SIZE[0], 50))
    terminal.blit(runButton, terminalPosition) # the run button, will probably replace this with an image
    pygame.draw.polygon(runButton, (255, 255, 255), [(8, 6), (8, 24), (23, 15)]) # the triangle within the run button
    screen.blit(terminal, (50, 50))

    # cursor
    cursorStartY = currentLineIndex * 45 + TERMINAL_PADDING[1] + 50
    cursorEndY = cursorStartY + font.get_height()
    cursor = pygame.draw.line(screen, (255, 255, 255), (cursorXOffset, cursorStartY), (cursorXOffset, cursorEndY), width=2)
    
    pygame.display.flip()
    clock.tick(60)
