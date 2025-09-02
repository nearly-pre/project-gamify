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

        self.setup()

    def setup(self):
        map = load_pygame(join('level_2_variables', 'data', 'maps', 'main.tmx'))

        image = pygame.image.load(join('level_2_variables', 'data', 'dialogs', 'next_button.png')).convert_alpha()
        self.nextButton = image
        self.nextButtonRect = self.nextButton.get_rect(topleft = (600, 590))

        for i in range(4):
            image = pygame.image.load(join('level_2_variables', 'data', 'dialogs', f'dialog{i}.png')).convert_alpha()
            self.dialogBoxes.append(image)

        self.objectiveBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective1.png')).convert_alpha())
        self.objectiveBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective2.png')).convert_alpha())
        self.objectiveCompleteBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective1_complete.png')).convert_alpha())
        self.objectiveCompleteBoxes.append(pygame.image.load(join('level_2_variables', 'data', 'images', 'objective2_complete.png')).convert_alpha())
        self.currentObjectiveImage = self.objectiveBoxes[0]
        self.currentObjectiveRect = (40, 40)

        mapWidth = map.width * TILE_SIZE
        mapHeight = map.height * TILE_SIZE
        self.internalSurface = pygame.Surface((mapWidth, mapHeight))

        for layer in ['Water', 'Island', 'Dirt', 'Outgrowth']:
            for x, y, image in map.get_layer_by_name(layer).tiles():
                Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.mapSprites)
        
        for layer in ['StructuresOne', 'StructuresTwo', 'StructuresThree', 'StructuresFour']:
            for x, y, image in map.get_layer_by_name(layer).tiles():
                CollisionSprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.collSprites, self.mapSprites))
        
        self.internalSurface.fill('black')
        self.mapSprites.draw(self.internalSurface)

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collSprites)

        for obj in map.get_layer_by_name('PlayerStartPosition'):
            if obj.name == "Player":
                self.player = Player((obj.x, obj.y), self.allSprites, self.collSprites,
                                     self.userControlledVariables["playerSpeed"])

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if not self.player.gameHasStarted:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            if self.nextButtonRect.collidepoint(pygame.mouse.get_pos()):
                                if self.dialogIndex == 3:
                                    self.player.gameHasStarted = True
                                    self.terminal = Terminal(deepcopy(self.userControlledVariables))
                                else:
                                    self.dialogIndex += 1

            if self.terminal:
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
                    
                    if newObjectiveCompleted:
                        self.objectiveFadeOut = True
                        self.objectiveAnimationTimer = pygame.time.get_ticks()

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
                        self.vignette.set_alpha(transparency - 5)
                    else:
                        self.vignetteTransitionMode = False
                else:
                    if transparency < 255:
                        self.vignette.set_alpha(transparency + 5)
                    else:
                        self.vignetteTransitionMode = False

            if self.objectiveFadeOut:
                if pygame.time.get_ticks() - self.objectiveAnimationTimer > 2000:
                    newX = self.currentObjectiveRect[0] - 720 * dt
                    self.currentObjectiveRect = (newX, self.currentObjectiveRect[1])
                    if newX <= -self.currentObjectiveImage.get_width():
                        self.objectiveFadeOut = False
                        if not self.objectivesComplete[1]:
                            self.objectiveFadeIn = True
                            self.objectiveAnimationTimer = pygame.time.get_ticks()
                            self.currentObjectiveImage = self.objectiveBoxes[1]

            elif self.objectiveFadeIn:
                if pygame.time.get_ticks() - self.objectiveAnimationTimer > 500:
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

            if not self.player.gameHasStarted:
                self.displaySurface.blit(self.dialogBoxes[self.dialogIndex], (0, 0))
                self.displaySurface.blit(self.nextButton, (600, 590))
            else:
                self.displaySurface.blit(self.currentObjectiveImage, self.currentObjectiveRect)

            pygame.display.flip()
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
