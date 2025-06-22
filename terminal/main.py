import pygame
from sys import exit
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

# constants
WIDTH = 1280
HEIGHT = 720
TAB = "   "
TERMINAL_PADDING = (30, 70)
TERMINAL_LINE_HEIGHT = 35
MINIMUM_TERMINAL_WIDTH = 500
MINIMUM_TERMINAL_HEIGHT = 300

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("python teacher")
clock = pygame.time.Clock()

# terminal
terminalSize = [640, 380]
terminal = pygame.Surface(terminalSize)
terminalRect = terminal.get_rect(topleft=(50, 50))
terminalPos = (50, 50)
resizeMargin = 5


runButton = pygame.image.load('./runButton.png')
runButtonRect = runButton.get_rect(topleft=(60, 60))

font = pygame.font.Font("./JetBrainsMono-Regular.ttf", 25)
lineSurfaces = [0]
codeLines = [""]
currentLineIndex = 0
backspaceDelayCounter = 0

# terminal actions
draggingTerminal = False
terminalResizing = False
resizingEdges = {"left": False, "right": False, "top": False, "bottom": False}

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

    mousePosX, mousePosY = pygame.mouse.get_pos()

    # check if the mouse is hovering over a terminal edge and set the cursor
    # accordingly. only run if we are not currently dragging or resizing.

    if not draggingTerminal and not terminalResizing:
        left = terminalPos[0]
        top = terminalPos[1]
        right = left + terminalSize[0]
        bottom = top + terminalSize[1]

        onLeftEdge = left - resizeMargin <= mousePosX <= left + resizeMargin
        onRightEdge = right - resizeMargin <= mousePosX <= right + resizeMargin
        onTopEdge = top - resizeMargin <= mousePosY <= top + resizeMargin
        onBottomEdge = bottom - resizeMargin <= mousePosY <= bottom + resizeMargin
        
        if (onLeftEdge and onTopEdge) or (onRightEdge and onBottomEdge):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENWSE)
        elif (onRightEdge and onTopEdge) or (onLeftEdge and onBottomEdge):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENESW)
        elif onLeftEdge or onRightEdge:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
        elif onTopEdge or onBottomEdge:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)


    for event in pygame.event.get():
        # window close handling
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # keystroke handling
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                continue # backspace handled in game loop

            # new code line
            elif event.key == pygame.K_RETURN:
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
                # ignoring keyboard shortcuts using isprintable()
                if event.unicode.isprintable(): 
                    codeLines[currentLineIndex] += event.unicode # event.unicode helps identify keyboard shortcuts
                
            lineSurfaces[currentLineIndex] = codeLineHighlight(codeLines[currentLineIndex])

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # checking if run button was pressed
                if runButtonRect.collidepoint((mousePosX, mousePosY)):
                    fullCode = "".join(codeLines)
                    try:
                        exec(fullCode) # code executed
                    except Exception as e:
                        print(f"An error occurred: {e}")


                # for terminal relocation
                elif terminalNavBar.collidepoint((mousePosX, mousePosY)):
                    draggingOffsetX = terminalNavBar.x - mousePosX
                    draggingOffsetY = terminalNavBar.y - mousePosY
                    draggingTerminal = True
                else:
                    left = terminalPos[0]
                    top = terminalPos[1]
                    right = left + terminalSize[0]
                    bottom = top + terminalSize[1]                    

                    if left - resizeMargin <= mousePosX <= left + resizeMargin:
                        resizingEdges["left"] = True
                    if right - resizeMargin <= mousePosX <= right + resizeMargin:
                        resizingEdges["right"] = True
                    if top - resizeMargin <= mousePosY <= top + resizeMargin:
                        resizingEdges["top"] = True
                    if bottom - resizeMargin <= mousePosY <= bottom + resizeMargin:
                        resizingEdges["bottom"] = True

                    if any(resizingEdges.values()):
                        terminalResizing = True
                        
        if event.type == pygame.MOUSEMOTION:
            if draggingTerminal:
                # performing checks on the X and Y position before actually moving the terminal
                # to that position. prevents the terminal from going off-screen.
                
                newPosX = draggingOffsetX + mousePosX
                newPosY = draggingOffsetY + mousePosY

                if newPosX < 0:
                    newPosX = 0
                elif newPosX > WIDTH - terminalSize[0]:
                    newPosX = WIDTH - terminalSize[0]

                if newPosY < 0:
                    newPosY = 0
                elif newPosY > HEIGHT - terminalSize[1]:
                    newPosY = HEIGHT - terminalSize[1]
                    
                terminalPos = (newPosX, newPosY)
                
            elif terminalResizing:
                sizeChanged = False
                rightEdge = terminalPos[0] + terminalSize[0]
                bottomEdge = terminalPos[1] + terminalSize[1]

                if resizingEdges["right"]:
                    newWidth = mousePosX - terminalPos[0]
                    if newWidth >= MINIMUM_TERMINAL_WIDTH:
                        terminalSize[0] = newWidth
                        sizeChanged = True

                if resizingEdges["left"]:
                    newWidth = rightEdge - mousePosX
                    if newWidth >= MINIMUM_TERMINAL_WIDTH:
                        terminalSize[0] = newWidth
                        terminalPos = (mousePosX, terminalPos[1])
                        sizeChanged = True

                if resizingEdges["bottom"]:
                    newHeight = mousePosY - terminalPos[1]
                    if newHeight >= MINIMUM_TERMINAL_HEIGHT:
                        terminalSize[1] = newHeight
                        sizeChanged = True

                if resizingEdges["top"]:
                    newHeight = bottomEdge - mousePosY
                    if newHeight >= MINIMUM_TERMINAL_HEIGHT:
                        terminalSize[1] = newHeight
                        terminalPos = (terminalPos[0], mousePosY)
                        sizeChanged = True
                
                if sizeChanged:
                    terminal = pygame.Surface(terminalSize)
                    terminal.fill((48, 44, 44))

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                draggingTerminal = False
                terminalResizing = False
                resizingEdges = {"left": False, "right": False, "top": False, "bottom": False}
        
            
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
                codeLines[currentLineIndex] = codeLines[currentLineIndex][:-1]
                lineSurfaces[currentLineIndex] = codeLineHighlight(codeLines[currentLineIndex])

            if codeLines[currentLineIndex] == "" and currentLineIndex != 0:
                codeLines.pop()
                lineSurfaces.pop()
                currentLineIndex -= 1

        backspaceDelayCounter += 1
    else:
        backspaceDelayCounter = 0


    # text blitting handled here
    for lineIndex, surfaces in enumerate(lineSurfaces):
        if surfaces:
            for surface, x in surfaces:
                terminal.blit(surface, (TERMINAL_PADDING[0] + x, lineIndex * TERMINAL_LINE_HEIGHT + TERMINAL_PADDING[1]))

    # cursor
    if codeLines[currentLineIndex]:
        # font.size calculates the font size without creating a surface. here, we call font.size
        # on the current codeLine, grab its width (x) using indexing (font.size returns a tuple)
        # and add it to other parameters affecting the horizontal offset.
        
        cursorOffsetX = font.size(codeLines[currentLineIndex])[0] + TERMINAL_PADDING[0]
    else:
        # case when no text has been entered in the terminal
        
        cursorOffsetX = TERMINAL_PADDING[0]

    # nav bar
    pygame.draw.rect(terminal, (58, 54, 54), (0, 0, terminalSize[0], 50))
    terminalNavBar = pygame.Rect(terminalPos[0], terminalPos[1], terminalSize[0], 50)

    # run button
    terminal.blit(runButton, (10, 10))
    runButtonRect = pygame.Rect(terminalPos[0] + 10, terminalPos[1] + 10, 31, 31)

    # cursor
    cursorStartY = currentLineIndex * TERMINAL_LINE_HEIGHT + TERMINAL_PADDING[1]
    cursorEndY = cursorStartY + font.get_height()
    cursor = pygame.draw.line(terminal, (255, 255, 255), (cursorOffsetX, cursorStartY), (cursorOffsetX, cursorEndY), width=2)

    # terminal
    terminalRect = screen.blit(terminal, terminalPos)

    pygame.display.flip()
    clock.tick(60)
