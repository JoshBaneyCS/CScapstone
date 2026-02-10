# ----- Imports -----
from enum import Enum
import pygame
import pygame_gui
from pygame_gui.core import ObjectID

class SceneID(Enum):
    """Enumeration for identifying different game scenes."""
    GAME_MENU = 1
    BLACKJACK = 2
    POKER = 3

# ----- Globals/Constants -----
BLACK = (0, 0, 0)
TOP_LEFT = (0, 0)

# Values assigned to chips for betting logic.
WHITE_CHIP_WORTH = 1
RED_CHIP_WORTH = 5
GREEN_CHIP_WORTH = 25
BLUE_CHIP_WORTH = 50
BLACK_CHIP_WORTH = 100

MENU_BUTTON_TEXT = 'Menu'
MENU_BUTTON_SIZE = (150, 50)
MENU_BUTTON_LOCATION = (1750 - MENU_BUTTON_SIZE[0] / 2, 50)

class Scene:
    """
    Base class for all game screens. Provides shared UI management and scene logic.
    """

    def __init__(self, game):
        """
        Initializes the scene, sets up the UI manager, and creates a parent container.

        Args:
            game: The main game GUI instance containing global settings and state.
        """
        self.game = game
        self.ui_manager = pygame_gui.UIManager(self.game.GAME_RESOLUTION, "theme.json")
        self.run_display = True

        # Use a panel as a parent container to manage all UI elements for this scene
        # as a single group. This allows for easier hiding/showing of entire screens.
        self.scene_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                (self.game.screen_width / 2 - self.game.GAME_RESOLUTION[0] / 2,
                 self.game.screen_height / 2 - self.game.GAME_RESOLUTION[1] / 2),
                self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            starting_height=0,
            container=self.game.canvas,
            object_id=ObjectID(class_id='@screen_background'))

        # Scenes start hidden and disabled until explicitly opened.
        self.scene_container.disable()
        self.scene_container.hide()

    def draw_scene(self):
        """Renders the scene background and UI elements to the main window."""
        self.game.window.fill(BLACK)
        self.ui_manager.draw_ui(self.game.window)
        pygame.display.update()

    def handle_events(self):
        """
        Processes pygame events.

        Note: Subclasses must implement this and should include settings menu logic.
        """
        raise NotImplementedError("Subclasses must implement 'handle_events(self)'")

    def update(self, time_delta):
        """
        Updates scene logic and the UI manager state.

        Args:
            time_delta (float): Time passed since the last frame.
        """
        self.update_scene()
        self.ui_manager.update(time_delta)

    def update_scene(self):
        """Handles scene-specific logic. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement 'update_scene(self)'")

    def open_scene(self):
        """Activates and displays the scene container."""
        self.scene_container.enable()
        self.scene_container.show()

    def close_scene(self):
        """Deactivates and hides the scene container."""
        self.scene_container.disable()
        self.scene_container.hide()

    def center_x(self, width):
        """
        Calculates the x-coordinate required to center an element horizontally.

        Args:
            width (int/float): The width of the element to be centered.

        Returns:
            float: The centered x-coordinate.
        """
        return self.game.GAME_HALF_WIDTH - (width / 2)

    def center_y(self, height):
        """
        Calculates the y-coordinate required to center an element vertically.

        Args:
            height (int/float): The height of the element to be centered.

        Returns:
            float: The centered y-coordinate.
        """
        return self.game.GAME_HALF_HEIGHT - (height / 2)

