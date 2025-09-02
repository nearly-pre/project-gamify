import pygame
from sys import exit
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token
from contextlib import redirect_stdout
from os.path import join
import io

class Terminal:
    def __init__(self, userControlledVariables, pos=(40, 250)):
        # constants
        self.WIDTH = 1280
        self.HEIGHT = 720
        self.TAB = "   "
        self.TERMINAL_PADDING = (30, 70)
        self.TERMINAL_LINE_HEIGHT = 35
        self.MINIMUM_TERMINAL_WIDTH = 500
        self.MINIMUM_TERMINAL_HEIGHT = 300

        # userControlledVariables should be a dictionary containing
        # the name and value of the variables that are to be modified
        # by the user
        self.userControlledVariables = userControlledVariables

        # terminal
        self.terminalSize = [500, 300]
        self.terminal = pygame.Surface(self.terminalSize, pygame.SRCALPHA) 
        self.terminalPos = pos
        self.terminalRect = self.terminal.get_rect(topleft=self.terminalPos)
        self.resizeMargin = 5

        self.runButton = pygame.image.load(join("terminal", "runButton.png"))
        self.runButtonRect = self.runButton.get_rect(topleft=(self.terminalPos[0] + 10, self.terminalPos[1] + 10))

        self.font = pygame.font.Font(join("terminal", "JetBrainsMono-Regular.ttf"), 25)
        self.lineSurfaces = [0]
        self.codeLines = [""]
        self.currentLineIndex = 0
        self.cursorColIndex = 0
        self.backspaceDelayCounter = 0
        self.deleteDelayCounter = 0

        self.isFocused = False

        # terminal actions
        self.draggingTerminal = False
        self.terminalResizing = False
        self.resizingEdges = {"left": False, "right": False, "top": False, "bottom": False}

        # output panel
        self.outputPanelVisible = False  # <-- Re-added: flag to control visibility
        self.outputPanelSize = (600, 400)
        self.outputPanelPos = ((self.WIDTH - self.outputPanelSize[0]) // 2, (self.HEIGHT - self.outputPanelSize[1]) // 2)
        self.outputPanelSurface = pygame.Surface(self.outputPanelSize, pygame.SRCALPHA)
        self.outputPanelRect = self.outputPanelSurface.get_rect(topleft=self.outputPanelPos)
        self.outputPanelCloseButtonRect = None
        self.outputLines = []
        self.outputTextColor = (220, 224, 230)
        
        self.outputTextColor = (220, 224, 230)
        self.errorTextColor = (255, 120, 120)
        self.successTextColor = (20, 255, 0)

        # initialize dragging offset
        self.draggingOffsetX = 0
        self.draggingOffsetY = 0

    def runUserCode(self, code):
        exec(code, {}, self.userControlledVariables)

    def codeLineHighlight(self, text):
        """function that highlights codes in real time, as the user types. it's not important to understand
        what the following code does. if youre really curious, search up lexing. this function will return
        a list "surfaces" containing all colored token surfaces."""

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
        if not self.draggingTerminal and not self.terminalResizing and not self.outputPanelVisible:
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

            if self.outputPanelVisible:
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.outputPanelCloseButtonRect and self.outputPanelCloseButtonRect.collidepoint(mousePosX, mousePosY):
                        self.outputPanelVisible = False
                continue 
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
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

                    if self.terminalRect.collidepoint((mousePosX, mousePosY)) and not self.terminalResizing:
                        if not self.terminalNavBar.collidepoint((mousePosX, mousePosY)):
                            self.isFocused = True
                            continue
                        else:
                            if self.runButtonRect.collidepoint((mousePosX, mousePosY)):
                                self.isFocused = True
                            else:
                                self.draggingOffsetX = self.terminalNavBar.x - mousePosX
                                self.draggingOffsetY = self.terminalNavBar.y - mousePosY
                                self.draggingTerminal = True
            
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
                            self.terminal.fill((48, 44, 44, 220))
            
            if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.draggingTerminal = False
                        self.terminalResizing = False
                        self.resizingEdges = {"left": False, "right": False, "top": False, "bottom": False}

            if self.isFocused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        continue  # backspace handled in game loop

                    elif event.key == pygame.K_LEFT:
                        if self.cursorColIndex > 0:
                            self.cursorColIndex -= 1
                        elif self.currentLineIndex > 0:
                            self.currentLineIndex -= 1
                            self.cursorColIndex = len(self.codeLines[self.currentLineIndex])
                        continue

                    elif event.key == pygame.K_RIGHT:
                        if self.cursorColIndex < len(self.codeLines[self.currentLineIndex]):
                            self.cursorColIndex += 1
                        elif self.currentLineIndex < len(self.codeLines) - 1:
                            self.currentLineIndex += 1
                            self.cursorColIndex = 0
                        continue

                    elif event.key == pygame.K_UP:
                        if self.currentLineIndex > 0:
                            self.currentLineIndex -= 1
                            self.cursorColIndex = min(self.cursorColIndex, len(self.codeLines[self.currentLineIndex]))
                        continue

                    elif event.key == pygame.K_DOWN:
                        if self.currentLineIndex < len(self.codeLines) - 1:
                            self.currentLineIndex += 1
                            self.cursorColIndex = min(self.cursorColIndex, len(self.codeLines[self.currentLineIndex]))
                        continue

                    elif event.key == pygame.K_RETURN:
                        textAfterCursor = self.codeLines[self.currentLineIndex][self.cursorColIndex:] 
                        currentLine = self.codeLines[self.currentLineIndex][:self.cursorColIndex]
                        self.codeLines[self.currentLineIndex] = currentLine
                        self.lineSurfaces[self.currentLineIndex] = self.codeLineHighlight(currentLine)

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
                        self.codeLines.insert(self.currentLineIndex, newLine)
                        self.lineSurfaces.insert(self.currentLineIndex, self.codeLineHighlight(newLine))
                        continue

                    elif event.key == pygame.K_TAB:
                        line = self.codeLines[self.currentLineIndex]
                        self.codeLines[self.currentLineIndex] = line[:self.cursorColIndex] + self.TAB + line[self.cursorColIndex:]
                        self.cursorColIndex += len(self.TAB)

                    else:
                        if event.unicode.isprintable():
                            line = self.codeLines[self.currentLineIndex]
                            self.codeLines[self.currentLineIndex] = line[:self.cursorColIndex] + event.unicode + line[self.cursorColIndex:]
                            self.cursorColIndex += len(event.unicode)

                    self.lineSurfaces[self.currentLineIndex] = self.codeLineHighlight(self.codeLines[self.currentLineIndex])

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:

                        if not self.terminalRect.collidepoint((mousePosX, mousePosY)):
                            self.isFocused = False
                            continue

                        # run the code
                        if self.runButtonRect.collidepoint((mousePosX, mousePosY)):
                            codeOutput = io.StringIO()
                            isError = False
                            
                            with redirect_stdout(codeOutput):
                                try:
                                    fullCode = "\n".join(self.codeLines)
                                    self.runUserCode(fullCode)
                                except Exception as e:
                                    print(f"Error executing code: {e}")
                                    isError = True
                            
                            outputText = codeOutput.getvalue()
                            if outputText == "":
                                outputText = "Success!"
                                textColor = self.successTextColor
                            else:
                                textColor = self.errorTextColor if isError else self.outputTextColor

                            self.outputLines = []
                            for line in outputText.splitlines():
                                lineSurface = self.font.render(line, True, textColor)
                                self.outputLines.append(lineSurface)

                            self.outputPanelVisible = True  # show output panel after running

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        # check if the close button of the output panel was clicked
                        if self.outputPanelVisible and self.outputPanelCloseButtonRect and self.outputPanelCloseButtonRect.collidepoint((mousePosX, mousePosY)):
                            self.outputPanelVisible = False

        # backspace handling
        textModified = False
        pressedKeys = pygame.key.get_pressed()

        if pressedKeys[pygame.K_BACKSPACE]:
            if not (self.backspaceDelayCounter % 15):
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

        if textModified:
            self.lineSurfaces[self.currentLineIndex] = self.codeLineHighlight(self.codeLines[self.currentLineIndex])

        # cursor logic
        textBeforeCursor = self.codeLines[self.currentLineIndex][:self.cursorColIndex]
        cursorOffsetX = self.font.size(textBeforeCursor)[0] + self.TERMINAL_PADDING[0]
        cursorStartY = self.currentLineIndex * self.TERMINAL_LINE_HEIGHT + self.TERMINAL_PADDING[1]
        cursorEndY = cursorStartY + self.font.get_height()

        if cursorEndY > self.terminalSize[1] - 20:
            self.terminalSize[1] += 50
            self.terminal = pygame.Surface(self.terminalSize, pygame.SRCALPHA)
            self.terminal.fill((48, 44, 44, 220))
        if cursorOffsetX > self.terminalSize[0] - 20:
            self.terminalSize[0] += 50
            self.terminal = pygame.Surface(self.terminalSize, pygame.SRCALPHA)
            self.terminal.fill((48, 44, 44, 220))

        # text blitting
        self.terminal.fill((48, 44, 44, 220))
        for lineIndex, surfaces in enumerate(self.lineSurfaces):
            if surfaces:
                for surface, x in surfaces:
                    self.terminal.blit(surface, (self.TERMINAL_PADDING[0] + x, lineIndex * self.TERMINAL_LINE_HEIGHT + self.TERMINAL_PADDING[1]))


        # drawing the cursor
        # i might add cursor blink later
        if self.isFocused:
            pygame.draw.line(self.terminal, (255, 255, 255), (cursorOffsetX, cursorStartY), (cursorOffsetX, cursorEndY), width=2)

        # nav bar
        pygame.draw.rect(self.terminal, (48, 44, 44, 222), (0, 0, self.terminalSize[0], 50))
        self.terminalNavBar = pygame.Rect(self.terminalPos[0], self.terminalPos[1], self.terminalSize[0], 50)

        # run button
        self.terminal.blit(self.runButton, (10, 10))
        self.runButtonRect = pygame.Rect(self.terminalPos[0] + 10, self.terminalPos[1] + 10, 31, 31)

        # blit terminal to screen
        self.terminalRect = screen.blit(self.terminal, self.terminalPos)

        # draw output panel if visible
        if self.outputPanelVisible:
            self.outputPanelSurface.fill((38, 38, 38, 200))
            pygame.draw.rect(self.outputPanelSurface, (80, 80, 80, 200), self.outputPanelSurface.get_rect(), 2)

            titleFont = pygame.font.Font(join("level_2_variables", "JetBrainsMono-Regular.ttf"), 20)
            titleSurface = titleFont.render("Output", True, (200, 200, 200))
            self.outputPanelSurface.blit(titleSurface, (10, 8))

            closeButtonSurface = titleFont.render("X", True, (255, 90, 90))
            closeButtonLocalRect = closeButtonSurface.get_rect(topright=(self.outputPanelSize[0] - 15, 8))
            self.outputPanelSurface.blit(closeButtonSurface, closeButtonLocalRect)

            self.outputPanelCloseButtonRect = pygame.Rect(
                self.outputPanelPos[0] + closeButtonLocalRect.x,
                self.outputPanelPos[1] + closeButtonLocalRect.y,
                closeButtonLocalRect.width,
                closeButtonLocalRect.height
            )

            yOffset = 40
            for lineSurface in self.outputLines:
                self.outputPanelSurface.blit(lineSurface, (15, yOffset))
                yOffset += self.font.get_height()
                if yOffset > self.outputPanelSize[1] - 15:
                    break
            screen.blit(self.outputPanelSurface, self.outputPanelPos)