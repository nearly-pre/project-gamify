from level_2_variables.settings import *
from level_2_variables.player import Player
from level_2_variables.sprites import CollisionSprite, Sprite
from level_2_variables.groups import AllSprites
from random import randint
from pytmx.util_pygame import load_pygame
from terminal.terminal import Terminal
from copy import deepcopy

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Variables")
        
        self.displaySurface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.allSprites = AllSprites()
        self.mapSprites = pygame.sprite.Group()
        self.collSprites = pygame.sprite.Group()

        self.dialogBoxes = []
        self.dialogIndex = 0

        self.objectiveBoxes = []
        self.objectiveCompleteBoxes = []
        self.objectivesComplete = [0, 0]
        self.objectiveIndex = 0
        self.objectiveFadeOut = False
        self.objectiveFadeIn = False

        self.objectivesDone = False
        self.gameOver = False
        self.gameOverTransition = False
        self.opacity = 0

        self.zoomScale = 5
        self.internalSurface = None

        self.vignette = pygame.image.load(join('level_2_variables', 'data', 'images', 'vignette.png')).convert_alpha()
        self.vignetteTransitionMode = False

        self.playerSpeed = 50
        self.playerIsBlind = True

        self.userControlledVariables = {
            "playerSpeed": self.playerSpeed,
            "playerIsBlind": self.playerIsBlind
        }

        self.terminal = None

        self.quizOptionFont = pygame.font.Font(join("level_2_variables", "data", "quiz", "BricolageGrotesque-SemiBold.ttf"), 46)
        self.quizQuestionFont = pygame.font.Font(join("level_2_variables", "data", "quiz", "BricolageGrotesque-SemiBold.ttf"), 52)
        self.optionAnsweredStates = [0, 0, 0, 0]
        self.swordImage = pygame.image.load(join('level_2_variables', 'data', 'quiz', 'sword.png')).convert_alpha()
        self.nextArrow = pygame.image.load(join('level_2_variables', 'data', 'quiz', 'nextArrow.png')).convert_alpha()
        self.backArrow = pygame.image.load(join('level_2_variables', 'data', 'quiz', 'backArrow.png')).convert_alpha()
        self.quizIndex = 0
        self.quizState = None
        self.quizStateChanged = False
        self.quizOver = False
        self.quizScore = 0

        self.timer = 0
        self.finalDialogStartTime = None

        self.setup()

    def setup(self):
        map = load_pygame(join('level_2_variables', 'data', 'maps', 'main.tmx'))

        # next button image
        image = pygame.image.load(join('level_2_variables', 'data', 'dialogs', 'next_button.png')).convert_alpha()
        self.nextButton = image
        self.nextButtonRect = self.nextButton.get_rect(topleft = (600, 590))

        # dialog boxes
        for i in range(9):
            image = pygame.image.load(join('level_2_variables', 'data', 'dialogs', f'dialog{i}.png')).convert_alpha()
            self.dialogBoxes.append(image)

        # objective boxes
        self.objectiveBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective1.png')).convert_alpha())
        self.objectiveBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective2.png')).convert_alpha())
        self.objectiveCompleteBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective1_complete.png')).convert_alpha())
        self.objectiveCompleteBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective2_complete.png')).convert_alpha())
        self.currentObjectiveImage = self.objectiveBoxes[0] # setting up initial objective
        self.currentObjectiveRect = (40, 40)

        mapWidth = map.width * TILE_SIZE
        mapHeight = map.height * TILE_SIZE
        self.internalSurface = pygame.Surface((mapWidth, mapHeight))

        # adding all layers
        for layer in ['Water', 'Island', 'Dirt', 'Outgrowth']:
            for x, y, image in map.get_layer_by_name(layer).tiles():
                Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.mapSprites)
        
        # adding all collision layers
        for layer in ['StructuresOne', 'StructuresTwo', 'StructuresThree', 'StructuresFour']:
            for x, y, image in map.get_layer_by_name(layer).tiles():
                CollisionSprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.collSprites, self.mapSprites))
        
        # drawing all layers
        self.internalSurface.fill('black')
        self.mapSprites.draw(self.internalSurface)

        # adding all invisible collision layers separately
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collSprites)

        # setting up player position
        for obj in map.get_layer_by_name('PlayerStartPosition'):
            if obj.name == "Player":
                self.player = Player((obj.x, obj.y), self.allSprites, self.collSprites,
                                     self.userControlledVariables["playerSpeed"])

    def drawQuiz(self, quiz, events):
        self.displaySurface.fill((254, 250, 231))

        keys = list(quiz.keys())
        questionType = quiz[keys[self.quizIndex]][5]

        mousePos = pygame.mouse.get_pos()
        leftMouseClicked = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                leftMouseClicked = True

        if questionType.lower() == "output" and not self.quizStateChanged:
            self.quizState = "output"
            self.quizStateChanged = True
        elif questionType.lower() == "normal" and not self.quizStateChanged:
            self.quizState = "normal"
            self.quizStateChanged = True

        if self.quizState == "output":
            question = self.quizQuestionFont.render("What will be the output?", True, (0, 0, 0))
            questionPosition = ((WINDOW_WIDTH / 2) - (question.get_width() / 2), 40)
            self.displaySurface.blit(question, questionPosition)

            commands = keys[self.quizIndex].split("; ")
            commandLineSurfaces = []
            longestCommandIndex = commands.index(max(commands, key=len))

            for i in commands:
                commandLineSurfaces.append(self.terminal.codeLineHighlight(i))

            longestCommandWidth, _ = self.terminal.font.size(commands[longestCommandIndex])
            codeLineHeight = 35
            terminalWidth = longestCommandWidth + 250
            terminalHeight = (len(commands) * codeLineHeight) + 145
            terminalX = (WINDOW_WIDTH / 2) - (terminalWidth / 2)
            terminalY = (WINDOW_HEIGHT / 2) - (terminalHeight / 2)
            
            terminalSurface = pygame.Surface((terminalWidth, terminalHeight), pygame.SRCALPHA)
            pygame.draw.rect(terminalSurface, (12, 13, 12), terminalSurface.get_rect(), border_radius=16)

            code = self.terminal.font.render("> Code", True, (220, 224, 230))
            terminalSurface.blit(code, (20, 20))

            for y, lineSurface in enumerate(commandLineSurfaces):
                for surface, x in lineSurface:
                    lineY = terminalHeight - 85 - (codeLineHeight * (len(commandLineSurfaces) - 1 - y))
                    terminalSurface.blit(surface, (60 + x, lineY)) 

            self.displaySurface.blit(terminalSurface, (terminalX, terminalY))

            nextArrowRect = self.displaySurface.blit(self.nextArrow, (1186, 46))
            if nextArrowRect.collidepoint(mousePos):
                if leftMouseClicked:
                    self.quizState = "normal"
        else:
            if questionType == "output":
                question = self.quizQuestionFont.render("What will be the output?", True, (0, 0, 0))
                questionPosition = ((WINDOW_WIDTH / 2) - (question.get_width() / 2), 40)
                self.displaySurface.blit(question, questionPosition)

                backArrowRect = self.displaySurface.blit(self.backArrow, (42, 46))
                if backArrowRect.collidepoint(mousePos):
                    if leftMouseClicked:
                        self.quizState = "output"
                        return
                            
            else: 
                questionLines = keys[self.quizIndex].split("\n")
                questionLineOneSurface = self.quizQuestionFont.render(questionLines[0], True, (0, 0, 0))
                questionLineTwoSurface = self.quizQuestionFont.render(questionLines[1], True, (0, 0, 0))

                questionLineOnePosition = ((WINDOW_WIDTH / 2) - (questionLineOneSurface.get_width() / 2), 40)
                questionLineTwoPosition = ((WINDOW_WIDTH / 2) - (questionLineTwoSurface.get_width() / 2), 95)

                self.displaySurface.blit(questionLineOneSurface, questionLineOnePosition)
                self.displaySurface.blit(questionLineTwoSurface, questionLineTwoPosition)

            options = quiz[keys[self.quizIndex]][:4]
            correctOption = quiz[keys[self.quizIndex]][4] - 1

            hoveringOnOption = False
            answered = any(self.optionAnsweredStates)
            wrongAnswerSelected = answered and self.optionAnsweredStates[correctOption] != 1

            if answered:
                nextArrowRect = self.displaySurface.blit(self.nextArrow, (1186, 46))
                if nextArrowRect.collidepoint(mousePos) and leftMouseClicked:
                    canProceed = True
                    if wrongAnswerSelected and pygame.time.get_ticks() - self.timer < 800:
                        canProceed = False

                    if canProceed:
                        if not wrongAnswerSelected:
                            self.quizScore += 1
                        self.quizIndex += 1
                        self.optionAnsweredStates = [0, 0, 0, 0]
                        self.quizStateChanged = False
                        
                        if self.quizIndex == len(keys):
                            self.quizOver = True
                        return

            optionRects = []
            optionHoveringStates = [0, 0, 0, 0]

            for i in range(4):
                optionRect = pygame.Rect(97, 200 + (i * 120), 1084, 102)
                optionRects.append(optionRect)

                isHovering = optionRect.collidepoint(mousePos) and not answered
                isCorrect = i == correctOption
                
                if isHovering and leftMouseClicked:
                    self.optionAnsweredStates[i] = 1
                    if not isCorrect:
                        self.timer = pygame.time.get_ticks()

                optionColor = (0, 0, 0)
                if isHovering:
                    optionColor = (189, 186, 177)
                
                if self.optionAnsweredStates[i] == 1:
                    if isCorrect:
                        optionColor = (79, 194, 35)
                    else:
                        optionColor = (225, 52, 52)
                elif answered and isCorrect:
                    if wrongAnswerSelected and pygame.time.get_ticks() - self.timer < 800:
                        optionColor = (0, 0, 0)
                    else:
                        optionColor = (79, 194, 35)

                pygame.draw.rect(self.displaySurface, optionColor, optionRect, border_radius=14)

                if isHovering:
                    hoveringOnOption = True
                    optionHoveringStates[i] = True
                    self.displaySurface.blit(self.swordImage, (122, optionRect.y + 24))
                    self.displaySurface.blit(self.swordImage, (1102, optionRect.y + 24))

            if hoveringOnOption:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            for i in range(4):
                textColor = (254, 250, 231)
                if optionHoveringStates[i]:
                    textColor = (0, 0, 0)
                
                textSurface = self.quizOptionFont.render(options[i], True, textColor)
                textRect = textSurface.get_rect(center=optionRects[i].center)
                self.displaySurface.blit(textSurface, textRect)


    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if not self.player.isMovable:
                    # check if next button is clicked
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            if self.nextButtonRect.collidepoint(pygame.mouse.get_pos()):
                                # start game if its the last dialog box
                                if self.dialogIndex == 3:
                                    self.player.isMovable = True
                                    self.terminal = Terminal(deepcopy(self.userControlledVariables))
                                
                                self.dialogIndex += 1
            
            if self.dialogIndex == 8 and not self.player.isMovable and not self.gameOverTransition:
                if self.finalDialogStartTime is None:
                    self.finalDialogStartTime = pygame.time.get_ticks()
                
                if pygame.time.get_ticks() - self.finalDialogStartTime > 1000:
                    self.gameOverTransition = True


            if not self.gameOver:
                if self.terminal:
                    # variable updated by user
                    if self.terminal.userControlledVariables != self.userControlledVariables:
                        self.terminal.isFocused = False
                        
                        self.userControlledVariables = deepcopy(self.terminal.userControlledVariables)
                        self.player.speed = self.userControlledVariables["playerSpeed"]
                        
                        newObjectiveCompleted = False
                        if not self.objectivesComplete[0] and not self.userControlledVariables["playerIsBlind"]:
                            self.currentObjectiveImage = self.objectiveCompleteBoxes[0]
                            self.objectivesComplete[0] = 1
                            newObjectiveCompleted = True
                        elif self.objectivesComplete[0] and not self.objectivesComplete[1] and self.player.speed >= 200:
                            self.currentObjectiveImage = self.objectiveCompleteBoxes[1]
                            self.objectivesComplete[1] = 1
                            newObjectiveCompleted = True
                        
                        # objective transition
                        if newObjectiveCompleted:
                            self.objectiveFadeOut = True
                            self.timer = pygame.time.get_ticks()

                        if self.playerIsBlind != self.userControlledVariables["playerIsBlind"]:
                            self.vignetteTransitionMode = True

                        self.playerIsBlind = self.userControlledVariables["playerIsBlind"]

                    if self.terminal.isFocused:
                        self.player.canMove = False
                    else:
                        self.player.canMove = True

                if self.vignetteTransitionMode:
                    transparency = self.vignette.get_alpha()

                    if not self.playerIsBlind: 
                        if transparency > 40:
                            self.vignette.set_alpha(transparency - 13 * dt)
                        else:
                            self.vignetteTransitionMode = False
                    else:
                        if transparency < 255:
                            self.vignette.set_alpha(transparency + 13 * dt)
                        else:
                            self.vignetteTransitionMode = False

                if self.objectiveFadeOut:
                    if pygame.time.get_ticks() - self.timer > 2000:
                        newX = self.currentObjectiveRect[0] - 720 * dt
                        self.currentObjectiveRect = (newX, self.currentObjectiveRect[1])
                        if newX <= -self.currentObjectiveImage.get_width():
                            self.objectiveFadeOut = False
                            if not self.objectivesComplete[1]:
                                self.objectiveFadeIn = True
                                self.timer = pygame.time.get_ticks()
                                self.currentObjectiveImage = self.objectiveBoxes[1]
                            else:
                                # if all objectives have been completed, game has finished
                                if all(self.objectiveBoxes):
                                    self.objectivesDone = True
                                    self.player.isMovable = False

                elif self.objectiveFadeIn:
                    if pygame.time.get_ticks() - self.timer > 500:
                        newX = self.currentObjectiveRect[0] + 720 * dt
                        self.currentObjectiveRect = (newX, self.currentObjectiveRect[1])
                        if newX >= 40:
                            self.currentObjectiveRect = (40, self.currentObjectiveRect[1])
                            self.objectiveFadeIn = False

                self.allSprites.update(dt)

                viewWidth = WINDOW_WIDTH / self.zoomScale
                viewHeight = WINDOW_HEIGHT / self.zoomScale
                
                cameraRect = pygame.Rect(0, 0, viewWidth, viewHeight)
                cameraRect.center = self.player.rect.center
                cameraRect.clamp_ip(self.internalSurface.get_rect())
                
                cameraView = self.internalSurface.subsurface(cameraRect)
                scaledSurface = pygame.transform.scale(cameraView, (WINDOW_WIDTH, WINDOW_HEIGHT))
                self.displaySurface.blit(scaledSurface, (0, 0))
                
                playerScaledWidth = self.player.rect.width * self.zoomScale
                playerScaledHeight = self.player.rect.height * self.zoomScale
                scaledPlayerImage = pygame.transform.scale(self.player.image, (int(playerScaledWidth), 
                                                                                int(playerScaledHeight)))
                
                playerScreenRect = scaledPlayerImage.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
                
                self.displaySurface.blit(scaledPlayerImage, playerScreenRect)
                self.displaySurface.blit(self.vignette, (0, 0))

                if self.terminal:
                    self.terminal.update(events, self.displaySurface)

                if not self.player.isMovable:
                    self.displaySurface.blit(self.dialogBoxes[self.dialogIndex], (0, 0))
                    if not self.gameOverTransition and self.dialogIndex != 8:
                        self.displaySurface.blit(self.nextButton, (600, 590))
                else:
                    self.displaySurface.blit(self.currentObjectiveImage, self.currentObjectiveRect)

                if self.gameOverTransition:
                    fadeSurface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    
                    self.opacity += 150 * dt  
                    self.opacity = min(self.opacity, 255)
                    
                    fadeSurface.fill((0, 0, 0, int(self.opacity)))
                    
                    self.displaySurface.blit(fadeSurface, (0, 0))
                    
                    if self.opacity >= 255:
                        self.gameOver = True


            else:           
                quiz = {
                    "Which of the following is an invalid\nvariable name in Python?": 
                        ["_total_score", "totalScore2", "total-score", "TotalScore", 3, "normal"],

                    "score = 50; score = 100; print(score)":
                        ["50", "100", "150", "error", 2, "output"],

                    "level = 1; print(Level)":
                        ["1", "0", "error", "Level", 3, "output"],
                    
                    "Which of the following is a valid\nvariable assignment in Python?":
                        ["player_health = 100", "player-health = 100", "player name = \"Bob\"", "1st_player = \"Bob\"", 1, "normal"],

                    "gold = 10; silver = 50; total_coins = gold + silver; print(total_coins)":
                        ["gold + silver", "10", "50", "60", 4, "output"],
                }

                self.terminal = Terminal(deepcopy(self.userControlledVariables))
                if not self.quizOver:
                    self.drawQuiz(quiz, events)
                else:
                    self.displaySurface.fill((254, 250, 231))
                    youScored = self.quizQuestionFont.render(f"You scored: ", True, (0, 0, 0))
                    score = self.quizQuestionFont.render(f"{self.quizScore}/5", True, (255, 191, 0)) 

                    youScoredPosition = ((WINDOW_WIDTH / 2) - (youScored.get_width() / 2), (WINDOW_HEIGHT / 2) - (youScored.get_height()))
                    scorePosition = ((WINDOW_WIDTH / 2) - (score.get_width() / 2), youScoredPosition[1] + youScored.get_height())

                    self.displaySurface.blit(youScored, youScoredPosition)
                    self.displaySurface.blit(score, scorePosition)


            pygame.display.flip()
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()