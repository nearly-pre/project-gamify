from level_2_variables.settings import *
import pygame
from os.path import join

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collSprites, speed):
        super().__init__(groups)

        playerIdleSheet = pygame.image.load(join('level_2_variables', 'data', 'images', 'idle_player.png')).convert_alpha()
        playerWalkSheet = pygame.image.load(join('level_2_variables', 'data', 'images', 'walk_player.png')).convert_alpha()

        self.frames = {
            'idle': [],
            'walk': []
        }

        self.frameIndex = 0
        self.animationType = "idle"
        self.canMove = True
        self.isMovable = False
        frameWidth = 96
        frameHeight = 64

        for i in range(9):
            idleFrame = playerIdleSheet.subsurface((i * frameWidth, 0, frameWidth, frameHeight))
            self.frames['idle'].append(idleFrame)

        for i in range(8):
            walkFrame = playerWalkSheet.subsurface((i * frameWidth, 0, frameWidth, frameHeight))
            self.frames['walk'].append(walkFrame)

        self.image = self.frames[self.animationType][self.frameIndex]
        self.rect = self.image.get_rect(topleft=pos)
        self.hitboxRect = self.rect.inflate(-80, -47)

        self.pos = pygame.Vector2(self.hitboxRect.topleft)

        self.direction = pygame.Vector2(0, 0)
        self.speed = speed

        self.collSprites = collSprites

    def input(self):
        keys = pygame.key.get_pressed()

        self.direction.x = keys[pygame.K_d] - keys[pygame.K_a]
        self.direction.y = keys[pygame.K_s] - keys[pygame.K_w]

        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

    def move(self, dt):
        # implementing maximum speed
        self.speed = 500 if self.speed > 500 else self.speed

        self.pos.x += self.direction.x * self.speed * dt
        self.hitboxRect.x = round(self.pos.x)
        self.collision("horizontal")

        self.pos.y += self.direction.y * self.speed * dt
        self.hitboxRect.y = round(self.pos.y)
        self.collision("vertical")

        self.rect.center = self.hitboxRect.center

    def collision(self, direction):
        for sprite in self.collSprites:
            if sprite.rect.colliderect(self.hitboxRect):
                if direction == 'horizontal':
                    if self.direction.x > 0: 
                        self.hitboxRect.right = sprite.rect.left
                        self.pos.x = self.hitboxRect.x 
                    if self.direction.x < 0: 
                        self.hitboxRect.left = sprite.rect.right
                        self.pos.x = self.hitboxRect.x 
                elif direction == 'vertical':
                    if self.direction.y > 0: 
                        self.hitboxRect.bottom = sprite.rect.top
                        self.pos.y = self.hitboxRect.y 
                    if self.direction.y < 0: 
                        self.hitboxRect.top = sprite.rect.bottom
                        self.pos.y = self.hitboxRect.y 

    def animate(self, dt):
        if self.direction:
            self.animationType = "walk"
        else:
            self.animationType = "idle"

        self.frameIndex += 30 * dt
        if self.frameIndex >= len(self.frames[self.animationType]):
            self.frameIndex = 0 

        self.image = self.frames[self.animationType][int(self.frameIndex)]

        if self.direction.x < 0:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, dt):
        if self.canMove and self.isMovable:
            self.input()
            self.move(dt)
        else:
            self.direction = pygame.Vector2(0, 0)
        self.animate(dt)
