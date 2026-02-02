import pygame
from menu import SceneID, LoginScreen, GameMenu, BlackjackScene


class Game:
    # ----- Global Variables -----
    GAME_NAME = "Capstone Casino"
    GAME_WIDTH = 1920
    GAME_HEIGHT = 1080
    GAME_HALF_WIDTH = GAME_WIDTH / 2
    GAME_HALF_HEIGHT = GAME_HEIGHT / 2
    GAME_RESOLUTION = (GAME_WIDTH, GAME_HEIGHT)

    def __init__(self):
        # ----- Pygame Setup -----
        pygame.init()
        pygame.display.set_caption(self.GAME_NAME)
        self.window =  pygame.display.set_mode(self.GAME_RESOLUTION, pygame.SCALED | pygame.FULLSCREEN)
        self.is_running, self.is_playing = True, False
        self.clock = pygame.time.Clock()
        self.scenes = {
            SceneID.LOGIN_SCREEN: LoginScreen(self),
            SceneID.GAME_MENU: GameMenu(self),
            SceneID.BLACKJACK: BlackjackScene(self)
        }
        self.current_scene = self.scenes[SceneID.LOGIN_SCREEN]
        self.current_scene.open_scene()

    def game_loop(self):
        while self.is_playing:
            time_delta = self.clock.tick(60) / 1000.0
            self.current_scene.handle_events()
            self.current_scene.update(time_delta)
            self.current_scene.draw_scene()

    def change_scene(self, scene_id):
        self.current_scene.close_scene()
        self.current_scene = self.scenes[scene_id]
        self.current_scene.open_scene()
