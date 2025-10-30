import pygame
import os
from pygamevideo import Video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
width, height, fps = 1920, 1080, 60

class Option:
    def __init__(self, text, rect, font, startDelay, fadeDuration=1.0):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.font = font
        self.startDelay = startDelay
        self.fadeDuration = fadeDuration
        self.alpha = 0
        self.visible = False
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

    def update(self, dt, totalElapsed):
        if totalElapsed < self.startDelay:
            return
        fadeElapsed = totalElapsed - self.startDelay
        frac = min(1.0, fadeElapsed / self.fadeDuration)
        self.alpha = int(255 * frac)
        self.visible = True

    def draw(self, screen, mousePos):
        if not self.visible:
            return
        hovered = self.rect.collidepoint(mousePos)
        bgColor = (18, 18, 18, self.alpha)
        if hovered:
            bgColor = (28, 28, 28, self.alpha)
        self.surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.surface, bgColor, self.surface.get_rect(), border_radius=16)
        textSurface = self.font.render(self.text, True, (250, 250, 250))
        textSurface.set_alpha(self.alpha)
        textRect = textSurface.get_rect(center=self.surface.get_rect().center)
        self.surface.blit(textSurface, textRect)
        screen.blit(self.surface, self.rect.topleft)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Physics")
        self.clock = pygame.time.Clock()
        self.running = False
        self.scenes = [
            Video(os.path.join(BASE_DIR, "sceneOne.mp4")),
            Video(os.path.join(BASE_DIR, "sceneTwo.mp4")),
            Video(os.path.join(BASE_DIR, "sceneThree.mp4")),
        ]

        self.sceneIndex = 0
        self.scenes[self.sceneIndex].play()
        self.font = pygame.font.Font(os.path.join(BASE_DIR, "cmu.ttf"), 42)
        self.correctVideoPaths = [
            os.path.join(BASE_DIR, "sceneCorrect.mp4"),
            os.path.join(BASE_DIR, "sceneCorrect2.mp4")
        ]
        self.wrongVideoPaths = [
            os.path.join(BASE_DIR, "sceneWrong.mp4"),
            os.path.join(BASE_DIR, "sceneWrong2.mp4")
        ]

        self.paused = False
        self.fadeTimer = 0.0
        self.quiz1Options = [
            Option("Light bends more towards the normal", (width//2 - 50, 340, 800, 120), self.font, startDelay=0.0),
            Option("Light bends less towards the normal", (width//2 - 50, 485, 800, 120), self.font, startDelay=0.6),
            Option("Light does not bend at all", (width//2 - 50, 630, 800, 120), self.font, startDelay=1.2),
        ]
        self.quiz1Correct = 0
        self.quiz2Options = [
            Option("Light will pass without bending", (width//2 - 50, 340, 800, 120), self.font, startDelay=0.0),
            Option("Light will bend toward the normal", (width//2 - 50, 485, 800, 120), self.font, startDelay=0.6),
            Option("Light will bend away from the normal", (width//2 - 50, 630, 800, 120), self.font, startDelay=1.2),
        ]
        self.quiz2Correct = 2
        self.options = self.quiz1Options
        self.correctOptionIndex = self.quiz1Correct
        self.feedbackVideo = None
        self.playingFeedback = False
        self.currentQuiz = None

    def drawQuiz(self, dt):
        self.fadeTimer += dt
        mousePos = pygame.mouse.get_pos()
        hovered = False
        for option in self.options:
            option.update(dt, self.fadeTimer)
            if option.visible and option.rect.collidepoint(mousePos):
                hovered = True
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hovered else pygame.SYSTEM_CURSOR_ARROW)
        for option in self.options:
            option.draw(self.screen, mousePos)

    def handleClick(self, pos):
        for i, option in enumerate(self.options):
            if option.visible and option.rect.collidepoint(pos):
                quizIdx = 0 if self.currentQuiz is None else self.currentQuiz
                correctPath = self.correctVideoPaths[quizIdx]
                wrongPath = self.wrongVideoPaths[quizIdx]
                chosenVideo = correctPath if i == self.correctOptionIndex else wrongPath
                self.feedbackVideo = Video(chosenVideo)
                self.feedbackVideo.play()
                self.playingFeedback = True
                break

    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                if self.paused and not self.playingFeedback and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handleClick(event.pos)
            if self.playingFeedback and self.feedbackVideo:
                self.feedbackVideo.draw_to(self.screen, (0, 0))
                if self.feedbackVideo.current_frame >= self.feedbackVideo.total_frames:
                    self.playingFeedback = False
                    self.feedbackVideo = None
                    if self.sceneIndex == 1:
                        self.sceneIndex = 2
                        self.scenes[self.sceneIndex].play()
                        self.paused = False
                        self.currentQuiz = None
                    elif self.sceneIndex == 2:
                        conclusion = Video(os.path.join(BASE_DIR, "conclusion.mp4"))
                        conclusion.play()
                        while conclusion.current_frame < conclusion.total_frames:
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    return
                            conclusion.draw_to(self.screen, (0, 0))
                            pygame.display.flip()
                            self.clock.tick(fps)
                        self.running = False
            else:
                scene = self.scenes[self.sceneIndex]
                scene.draw_to(self.screen, (0, 0))
                isOver = scene.current_frame >= scene.total_frames - 1
                if isOver and not self.paused:
                    if self.sceneIndex == 0:
                        self.sceneIndex = 1
                        self.scenes[self.sceneIndex].play()
                    elif self.sceneIndex == 1:
                        scene.pause()
                        self.paused = True
                        self.fadeTimer = 0.0
                        self.options = self.quiz1Options
                        self.correctOptionIndex = self.quiz1Correct
                        self.currentQuiz = 0
                    elif self.sceneIndex == 2:
                        scene.pause()
                        self.paused = True
                        self.fadeTimer = 0.0
                        self.options = self.quiz2Options
                        self.correctOptionIndex = self.quiz2Correct
                        self.currentQuiz = 1
                if self.paused:
                    self.drawQuiz(dt)
            pygame.display.flip()
        self.quit()

    def quit(self):
        pygame.quit()

if __name__ == "__main__":
    Game().run()
