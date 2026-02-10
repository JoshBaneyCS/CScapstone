# ----- Imports -----
import pygame
import pygame_gui

from scene import SceneID
from blackjack import BlackjackScene
from game_menu import GameMenu
from poker import PokerScene

# ----- Global Card Identifier Pieces  -----
# These lists are used to programmatically generate file paths and dictionary keys.
suits = ['H', 'D', 'C', 'S']
ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
colors = ['red', 'blue', 'green', 'black', 'orange', 'purple']

class Game:
    """
    The GUI engine for the Capstone Casino.

    This class initializes the Pygame environment, manages the main window state,
    pre-loads assets (cards), and handles the transitions between different game scenes.
    """

    # ----- Globals/Constants -----
    GAME_NAME = "Capstone Casino"
    GAME_WIDTH = 1920
    GAME_HEIGHT = 1080
    GAME_HALF_WIDTH = GAME_WIDTH / 2
    GAME_HALF_HEIGHT = GAME_HEIGHT / 2
    GAME_RESOLUTION = (GAME_WIDTH, GAME_HEIGHT)
    CANVAS_ORIGIN_LOCATION = (0,0)
    FRAMES_PER_SECOND = 60

    def __init__(self):
        """
        Initializes the game engine, display settings, and asset dictionaries.
        """

        # Initialize core Pygame modules and set window caption.
        pygame.init()
        pygame.display.set_caption(self.GAME_NAME)

        # Detect system resolution to support dynamic fullscreen scaling.
        display_info = pygame.display.Info()
        self.screen_width = display_info.current_w
        self.screen_height = display_info.current_h
        screen_resolution = (self.screen_width, self.screen_height)

        self.window = pygame.display.set_mode(screen_resolution, pygame.FULLSCREEN)
        self.ui_manager = pygame_gui.UIManager(screen_resolution)
        self.time_delta = 0

        # Main background panel that spans the entire screen.
        self.canvas = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.CANVAS_ORIGIN_LOCATION, screen_resolution),
            manager=self.ui_manager,
            starting_height=0)
        self.is_running, self.is_playing = True, False
        self.clock = pygame.time.Clock()

        # Pre-load card assets into memory to prevent lag during gameplay.
        # Format: 'AS' for Ace of Spades, '10H' for Ten of Hearts, etc.
        self.cardDict = {f"{rank}{suit}": pygame.image.load(f"resources/images/Cards/{rank}{suit}.png").convert_alpha() for suit in suits for rank in ranks}

        # Pre-load card back variations.
        self.backingDict = {f"{color}": pygame.image.load(f"resources/images/Cards/Card Back/card back {color}.png").convert_alpha() for color in colors}

        # Scene Registry: Initialize all GUI states.
        self.scenes = {
            SceneID.GAME_MENU: GameMenu(self),
            SceneID.BLACKJACK: BlackjackScene(self),
            SceneID.POKER: PokerScene(self)
        }

        # Set the starting scene to the Main Menu.
        self.current_scene = self.scenes[SceneID.GAME_MENU]
        self.current_scene.open_scene()

    def game_loop(self):
        """
        The primary execution loop of the GUI.

        Coordinates the timing, event handling, logic updates, and
        rendering for the currently active scene.
        """
        while self.is_playing:
            # Calculate time since last frame in seconds for smooth movement/animations.
            self.time_delta = self.clock.tick(self.FRAMES_PER_SECOND) / 1000.0

            self.current_scene.handle_events()
            self.current_scene.update(self.time_delta)
            self.current_scene.draw_scene()

    def change_scene(self, scene_id):
        """
        Transitions the display from the current scene to a new one.

        Args:
            scene_id (SceneID): The ID of the scene to switch to.
        """
        self.current_scene.close_scene()
        self.current_scene = self.scenes[scene_id]
        self.current_scene.open_scene()
