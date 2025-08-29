import pygame
from sys import exit
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token
from contextlib import redirect_stdout
import io

class Terminal:
    def __init__(self, pos=(50, 50)):
        # constants
        self.WIDTH = 1280
        self.HEIGHT = 720
        self.TAB = "   "
        self.TERMINAL_PADDING = (30, 70)
        self.TERMINAL_LINE_HEIGHT = 35
        self.MINIMUM_TERMINAL_WIDTH = 500
        self.MINIMUM_TERMINAL_HEIGHT = 300

        # terminal
        self.terminalSize = [640, 400]
        self.terminal = pygame.Surface(self.terminalSize, pygame.SRCALPHA) 
        self.terminalPos = pos
        self.terminalRect = self.terminal.get_rect(topleft=self.terminalPos)
        self.resizeMargin = 5

        self.runButton = pygame.image.load('./runButton.png')
        self.runButtonRect = self.runButton.get_rect(topleft=(self.terminalPos[0] + 10, self.terminalPos[1] + 10))

        self.font = pygame.font.Font("./JetBrainsMono-Regular.ttf", 25)
        self.lineSurfaces = [0]
        self.codeLines = [""]
        self.currentLineIndex = 0
        self.cursorColIndex = 0
        self.backspaceDelayCounter = 0
        self.deleteDelayCounter = 0

        self.outputTextColor = (220, 224, 230)
        self.errorTextColor = (255, 120, 120)

        # terminal actions
        self.draggingTerminal = False
        self.terminalResizing = False
        self.resizingEdges = {"left": False, "right": False, "top": False, "bottom": False}

        # output panel
        self.outputPanelSize = (600, 400)
        self.outputPanelPos = ((self.WIDTH - self.outputPanelSize[0]) // 2, (self.HEIGHT - self.outputPanelSize[1]) // 2)
        self.outputPanelSurface = pygame.Surface(self.outputPanelSize, pygame.SRCALPHA)
        self.outputPanelRect = self.outputPanelSurface.get_rect(topleft=self.outputPanelPos)
        self.outputPanelCloseButtonRect = None
        self.outputLines = []
        self.outputTextColor = (220, 224, 230)
        self.errorTextColor = (255, 120, 120)

        # initialize dragging offset
        self.draggingOffsetX = 0
        self.draggingOffsetY = 0

    def codeLineHighlight(self, text):
        """Function that highlights codes in real-time, as the user types. It's not important to understand
        what the following code does. If you're really curious, search up lexing. This function will return
        a list 'surfaces' containing all colored token surfaces."""

        # all the token colors. Chat-gpted, obviously.
        tokenColors = {
            Token.Keyword: (186, 218, 85),
            Token.Keyword.Namespace: (186, 218, 85),
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
            Token.Comment.Single: (98, 114, 130),
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
            tokenSurface = self.font.render(tokenValue, True, color)
            surfaces.append((tokenSurface, x))
            x += tokenSurface.get_width()

        return surfaces

    def update(self, events, screen):
        mousePosX, mousePosY = pygame.mouse.get_pos()

        # check if the mouse is hovering over a terminal edge and set the cursor
        # accordingly. only run if we are not currently dragging or resizing.
        if not self.draggingTerminal and not self.terminalResizing:
            left = self.terminalPos[0]
            top = self.terminalPos[1]
            right = left + self.terminalSize[0]
            bottom = top + self.terminalSize[1]

            onLeftEdge = left - self.resizeMargin <= mousePosX <= left + self.resizeMargin
            onRightEdge = right - self.resizeMargin <= mousePosX <= right + self.resizeMargin
            onTopEdge = top - self.resizeMargin <= mousePosY <= top + self.resizeMargin
            onBottomEdge = bottom - self.resizeMargin <= mousePosY <= bottom + self.resizeMargin

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

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                    continue  # backspace and delete handled in game loop

                elif event.key == pygame.K_LEFT:
                    # if the left key is pressed, move the cursor to the left

                    if self.cursorColIndex > 0:
                        self.cursorColIndex -= 1
                    elif self.currentLineIndex > 0:
                        self.currentLineIndex -= 1
                        self.cursorColIndex = len(self.codeLines[self.currentLineIndex])
                    continue

                elif event.key == pygame.K_RIGHT:
                    # if the right key is pressed, move the cursor to the right

                    if self.cursorColIndex < len(self.codeLines[self.currentLineIndex]):
                        self.cursorColIndex += 1
                    elif self.currentLineIndex < len(self.codeLines) - 1:
                        self.currentLineIndex += 1
                        self.cursorColIndex = 0
                    continue

                elif event.key == pygame.K_UP:
                    # if the up key is pressed, move the cursor up by a line

                    if self.currentLineIndex > 0:
                        self.currentLineIndex -= 1
                        # when the user moves up, the horizontal cursor position has to change 
                        # IF the line above is smaller in length

                        self.cursorColIndex = min(self.cursorColIndex, len(self.codeLines[self.currentLineIndex]))
                    continue

                elif event.key == pygame.K_DOWN:
                    # if the down key is pressed, move the cursor down by a line

                    if self.currentLineIndex < len(self.codeLines) - 1:
                        self.currentLineIndex += 1
                        self.cursorColIndex = min(self.cursorColIndex, len(self.codeLines[self.currentLineIndex]))
                    continue

                elif event.key == pygame.K_RETURN:
                    # new code line

                    textAfterCursor = self.codeLines[self.currentLineIndex][self.cursorColIndex:] 
                    currentLine = self.codeLines[self.currentLineIndex][:self.cursorColIndex]
                    self.codeLines[self.currentLineIndex] = currentLine
                    self.lineSurfaces[self.currentLineIndex] = self.codeLineHighlight(currentLine)

                    # auto-indentation feature
                    newIndentation = ""
                    for char in currentLine:
                        if char != " ":
                            break
                        else:
                            newIndentation += " "
                    if currentLine.strip().endswith(":"):
                        newIndentation += self.TAB

                    self.currentLineIndex += 1
                    self.cursorColIndex = len(newIndentation)

                    newLine = newIndentation + textAfterCursor
                    self.codeLines[self.currentLineIndex] = newLine
                    self.lineSurfaces[self.currentLineIndex] = self.codeLineHighlight(newLine)

                    continue

                elif event.key == pygame.K_TAB:
                    # indentation

                    line = self.codeLines[self.currentLineIndex]
                    self.codeLines[self.currentLineIndex] = line[:self.cursorColIndex] + self.TAB + line[self.cursorColIndex:]
                    self.cursorColIndex += len(self.TAB)

                else:
                    # only print unicode printable characters. fixes a glitch

                    if event.unicode.isprintable():
                        line = self.codeLines[self.currentLineIndex]
                        self.codeLines[self.currentLineIndex] = line[:self.cursorColIndex] + event.unicode + line[self.cursorColIndex:]
                        self.cursorColIndex += len(event.unicode)

                # after all events have been processed, highlight the line
                
                self.lineSurfaces[self.currentLineIndex] = self.codeLineHighlight(self.codeLines[self.currentLineIndex])

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    # run the code
                    if self.runButtonRect.collidepoint((mousePosX, mousePosY)):
                        outputLines = []
                        codeOutput = io.StringIO()
                        isError = False
                        
                        with redirect_stdout(codeOutput):
                            try:
                                fullCode = "\n".join(self.codeLines)
                                exec(fullCode) # code executed
                            except Exception as e:
                                print(f"Error executing code: {e}")
                                isError = True
                        
                        outputText = codeOutput.getvalue()
                        textColor = self.errorTextColor if isError else self.outputTextColor

                        for line in outputText.splitlines():
                            lineSurface = self.font.render(line, True, textColor)
                            outputLines.append(lineSurface)
                        
                    elif self.terminalNavBar.collidepoint((mousePosX, mousePosY)):
                        self.draggingOffsetX = self.terminalNavBar.x - mousePosX
                        self.draggingOffsetY = self.terminalNavBar.y - mousePosY
                        self.draggingTerminal = True
                    else:
                        # terminal resizing

                        left = self.terminalPos[0]
                        top = self.terminalPos[1]
                        right = left + self.terminalSize[0]
                        bottom = top + self.terminalSize[1]

                        if left - self.resizeMargin <= mousePosX <= left + self.resizeMargin:
                            self.resizingEdges["left"] = True
                        if right - self.resizeMargin <= mousePosX <= right + self.resizeMargin:
                            self.resizingEdges["right"] = True
                        if top - self.resizeMargin <= mousePosY <= top + self.resizeMargin:
                            self.resizingEdges["top"] = True
                        if bottom - self.resizeMargin <= mousePosY <= bottom + self.resizeMargin:
                            self.resizingEdges["bottom"] = True

                        if any(self.resizingEdges.values()):
                            self.terminalResizing = True

            if event.type == pygame.MOUSEMOTION:
                if self.draggingTerminal:
                    newPosX = self.draggingOffsetX + mousePosX
                    newPosY = self.draggingOffsetY + mousePosY

                    if newPosX < 0:
                        newPosX = 0
                    elif newPosX > self.WIDTH - self.terminalSize[0]:
                        newPosX = self.WIDTH - self.terminalSize[0]

                    if newPosY < 0:
                        newPosY = 0
                    elif newPosY > self.HEIGHT - self.terminalSize[1]:
                        newPosY = self.HEIGHT - self.terminalSize[1]

                    self.terminalPos = (newPosX, newPosY)

                elif self.terminalResizing:
                    sizeChanged = False
                    rightEdge = self.terminalPos[0] + self.terminalSize[0]
                    bottomEdge = self.terminalPos[1] + self.terminalSize[1]

                    if self.resizingEdges["right"]:
                        newWidth = mousePosX - self.terminalPos[0]
                        if newWidth >= self.MINIMUM_TERMINAL_WIDTH:
                            self.terminalSize[0] = newWidth
                            sizeChanged = True

                    if self.resizingEdges["left"]:
                        newWidth = rightEdge - mousePosX
                        if newWidth >= self.MINIMUM_TERMINAL_WIDTH:
                            self.terminalSize[0] = newWidth
                            self.terminalPos = (mousePosX, self.terminalPos[1])
                            sizeChanged = True

                    if self.resizingEdges["bottom"]:
                        newHeight = mousePosY - self.terminalPos[1]
                        if newHeight >= self.MINIMUM_TERMINAL_HEIGHT:
                            self.terminalSize[1] = newHeight
                            sizeChanged = True

                    if self.resizingEdges["top"]:
                        newHeight = bottomEdge - mousePosY
                        if newHeight >= self.MINIMUM_TERMINAL_HEIGHT:
                            self.terminalSize[1] = newHeight
                            self.terminalPos = (self.terminalPos[0], mousePosY)
                            sizeChanged = True

                    if sizeChanged:
                        self.terminal = pygame.Surface(self.terminalSize, pygame.SRCALPHA)
                        self.terminal.fill((48, 44, 44, 230))

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.draggingTerminal = False
                    self.terminalResizing = False
                    self.resizingEdges = {"left": False, "right": False, "top": False, "bottom": False}

        # Backspace and delete handling
        textModified = False
        pressedKeys = pygame.key.get_pressed()

        if pressedKeys[pygame.K_BACKSPACE]:
            if not (self.backspaceDelayCounter % 5):
                if pressedKeys[pygame.K_LCTRL]:
                    if self.cursorColIndex > 0:
                        currentLine = self.codeLines[self.currentLineIndex]
                        textBeforeCursor = currentLine[:self.cursorColIndex]
                        i = len(textBeforeCursor) - 1
                        while i >= 0 and textBeforeCursor[i].isspace():
                            i -= 1
                        while i >= 0 and not textBeforeCursor[i].isspace():
                            i -= 1

                        newCursorPos = i + 1
                        self.codeLines[self.currentLineIndex] = currentLine[:newCursorPos] + currentLine[self.cursorColIndex:]
                        self.cursorColIndex = newCursorPos
                        textModified = True
                else:
                    if self.cursorColIndex > 0:
                        currentLine = self.codeLines[self.currentLineIndex]
                        self.codeLines[self.currentLineIndex] = currentLine[:self.cursorColIndex - 1] + currentLine[self.cursorColIndex:]
                        self.cursorColIndex -= 1
                        textModified = True
                    elif self.currentLineIndex > 0:
                        textToAppend = self.codeLines.pop(self.currentLineIndex)
                        self.lineSurfaces.pop(self.currentLineIndex)
                        self.currentLineIndex -= 1
                        newCursorPos = len(self.codeLines[self.currentLineIndex])
                        self.codeLines[self.currentLineIndex] += textToAppend
                        self.cursorColIndex = newCursorPos
                        textModified = True

            self.backspaceDelayCounter += 1
        else:
            self.backspaceDelayCounter = 0

        if pressedKeys[pygame.K_DELETE]:
            if not (self.deleteDelayCounter % 5):
                currentLine = self.codeLines[self.currentLineIndex]
                if self.cursorColIndex < len(currentLine):
                    self.codeLines[self.currentLineIndex] = currentLine[:self.cursorColIndex] + currentLine[self.cursorColIndex + 1:]
                    textModified = True
                elif self.currentLineIndex < len(self.codeLines) - 1:
                    textToAppend = self.codeLines.pop(self.currentLineIndex + 1)
                    self.lineSurfaces.pop(self.currentLineIndex + 1)
                    self.codeLines[self.currentLineIndex] += textToAppend
                    textModified = True
            self.deleteDelayCounter += 1
        else:
            self.deleteDelayCounter = 0

        if textModified:
            self.lineSurfaces[self.currentLineIndex] = self.codeLineHighlight(self.codeLines[self.currentLineIndex])

        # cursor logic
        textBeforeCursor = self.codeLines[self.currentLineIndex][:self.cursorColIndex]
        cursorOffsetX = self.font.size(textBeforeCursor)[0] + self.TERMINAL_PADDING[0]

        cursorStartY = self.currentLineIndex * self.TERMINAL_LINE_HEIGHT + self.TERMINAL_PADDING[1]
        cursorEndY = cursorStartY + self.font.get_height()
        cursor = pygame.draw.line(self.terminal, (255, 255, 255), (cursorOffsetX, cursorStartY), (cursorOffsetX, cursorEndY), width=2)

        if cursorEndY > self.terminalSize[1] - 20:
            self.terminalSize[1] += 50
            self.terminal = pygame.Surface(self.terminalSize, pygame.SRCALPHA)
            self.terminal.fill((48, 44, 44, 230))
        if cursorOffsetX > self.terminalSize[0] - 20:
            self.terminalSize[0] += 50
            self.terminal = pygame.Surface(self.terminalSize, pygame.SRCALPHA)
            self.terminal.fill((48, 44, 44, 230))

        # text blitting
        self.terminal.fill((48, 44, 44, 230))
        for lineIndex, surfaces in enumerate(self.lineSurfaces):
            if surfaces:
                for surface, x in surfaces:
                    self.terminal.blit(surface, (self.TERMINAL_PADDING[0] + x, lineIndex * self.TERMINAL_LINE_HEIGHT + self.TERMINAL_PADDING[1]))

        # nav bar
        pygame.draw.rect(self.terminal, (48, 44, 44, 240), (0, 0, self.terminalSize[0], 50))
        self.terminalNavBar = pygame.Rect(self.terminalPos[0], self.terminalPos[1], self.terminalSize[0], 50)

        # run button
        self.terminal.blit(self.runButton, (10, 10))
        self.runButtonRect = pygame.Rect(self.terminalPos[0] + 10, self.terminalPos[1] + 10, 31, 31)

        # blit terminal to screen
        self.terminalRect = screen.blit(self.terminal, self.terminalPos)
