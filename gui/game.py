## TODO: Replace "magic" numbers with constants for easier maintainability/searching (applies to all files)
import pygame
import pygame_gui
from scene import SceneID, LoginScreen, GameMenu, BlackjackScene

# ----- Global Card Identifier Pieces  -----
## used by the card/card backing dictionaries
suits = ['H', 'D', 'C', 'S']
ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
colors = ['red', 'blue', 'green', 'black', 'orange', 'purple']

## Sets up and runs GUI for the game
## Responsible for managing the different scenes (login, game selection, blackjack, poker)
class Game:
    # ----- Globals/Constants -----
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
        display_info = pygame.display.Info()
        self.screen_width = display_info.current_w
        self.screen_height = display_info.current_h
        screen_resolution = (self.screen_width, self.screen_height)
        ## TODO: remove after confirming resolution changes in dev-test
        #self.window =  pygame.display.set_mode(self.GAME_RESOLUTION, pygame.SCALED | pygame.FULLSCREEN)
        self.window = pygame.display.set_mode(screen_resolution, pygame.FULLSCREEN)
        self.ui_manager = pygame_gui.UIManager(screen_resolution)
        self.canvas = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), screen_resolution),
            manager=self.ui_manager,
            starting_height=0)
        self.is_running, self.is_playing = True, False
        self.clock = pygame.time.Clock()

        self.cardDict = {f"{rank}{suit}": pygame.image.load(f"resources/images/Cards/{rank}{suit}.png").convert_alpha() for suit in suits for rank in ranks}
        self.backingDict = {f"{color}": pygame.image.load(f"resources/images/Cards/Card Back/card back {color}.png").convert_alpha() for color in colors}

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
