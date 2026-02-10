# ----- Imports -----
import pygame
import pygame_gui
from pygame_gui.core import ObjectID

# ----- Globals/Constants -----
CARD_WIDTH = 140
CARD_HEIGHT = 215
CARD_SIZE = (CARD_WIDTH, CARD_HEIGHT)

# Constants for the flip animation logic
FLIP_SIZE_DELTA = 8  # How many pixels the card shrinks/grows per frame during a flip
FLIP_X_DELTA = 4     # How much the x-position shifts to keep the shrinking card centered
CARD_MOVE_SPEED = 1
MOVE_DURATION = 2.0  # Time in seconds for a card to complete its travel

class Card:
    """
    Represents a physical card in the game with built-in animations.

    Handles loading front/back textures, moving between coordinates using
    interpolation, and a pseudo-3D flipping animation.
    """

    def __init__(self, scene, location):
        """
        Initializes the card and its UI containers.

        Args:
            scene: The current Scene object this card belongs to.
            location (tuple): The initial (x, y) coordinates for the card.
        """
        self.front_surface: pygame.Surface = None
        self.back_surface: pygame.Surface = None

        # State management for animations
        self.flipping, self.flipped, self.front_showing = False, False, False
        self.moving, self.move_then_flip = False, False

        # Vector-based positioning for smooth movement logic
        self.start_location = pygame.Vector2(location)
        self.target_location = pygame.Vector2(0,0)
        self.move_time = 0.0

        self.scene = scene

        # The container allows the card and its shadow/border to move as one unit
        self.card_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(location, (CARD_WIDTH+4, CARD_HEIGHT+4)),
            manager=self.scene.ui_manager,
            starting_height=0,
            container=self.scene.scene_container,
            object_id=ObjectID(class_id='@card_container'))

        self.set_back("red")

        # The actual image element that displays the card texture
        self.image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect((0,0), CARD_SIZE),
            image_surface= self.back_surface,
            manager=self.scene.ui_manager,
            container=self.card_container,
            object_id=ObjectID(class_id='@card'))

    def toggle_card_visibility(self):
        """Hides or shows the entire card container and its contents."""
        self.image.visible = not self.image.visible
        self.card_container.visible = not self.card_container.visible

    def set_front(self, identifier):
        """
        Sets the front texture of the card from the game asset dictionary.

        Args:
            identifier (str): The rank/suit key (e.g., 'AH', '10S').
        """
        card_image = self.scene.game.cardDict.get(identifier)
        self.front_surface = pygame.transform.scale(card_image, CARD_SIZE)

    def set_back(self, color):
        """
        Sets the back texture of the card.

        Args:
            color (str): The color key for the card back (e.g., 'red', 'blue').
        """
        back_image = self.scene.game.backingDict.get(color)
        self.back_surface = pygame.transform.scale(back_image, CARD_SIZE)

    def change_card_image(self, card_surface, size_change, position_change):
        """
        Helper method to recreate the UIImage during a flipping animation.

        This simulates a 3D rotation by narrowing the width of the image.
        """

        self.image.kill()  # Remove the old image element from the UI manager

        new_x = self.image.relative_rect.x + position_change
        new_location = (new_x, 0)
        new_width = self.image.relative_rect.width + size_change
        new_size = (new_width, CARD_HEIGHT)

        # Scale the texture to the new narrow width
        scaled_surface = pygame.transform.scale(card_surface, (new_width, CARD_HEIGHT))

        self.image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(new_location, new_size),
            image_surface=scaled_surface,
            manager=self.scene.ui_manager,
            container=self.card_container,
            object_id=ObjectID(class_id='@card'))

    def flip_card(self):
        """
        Iterative animation step for flipping the card.

        Shrinks the card to a sliver, swaps the texture (front/back),
        and then expands it back to full width.
        """
        if not self.flipped:
            if not self.front_showing:
                # Shrink back surface
                self.change_card_image(self.back_surface, -FLIP_SIZE_DELTA, FLIP_X_DELTA)
                if self.image.relative_rect.width <= FLIP_SIZE_DELTA:
                    self.front_showing = True
            else:
                # Expand front surface
                self.change_card_image(self.front_surface, FLIP_SIZE_DELTA, -FLIP_X_DELTA)
                if self.image.relative_rect.width >= CARD_WIDTH:
                    self.flipped, self.flipping = True, False
        else:
            if self.front_showing:
                # Shrink front surface
                self.change_card_image(self.front_surface, -FLIP_SIZE_DELTA, FLIP_X_DELTA)
                if self.image.relative_rect.width <= FLIP_SIZE_DELTA:
                    self.front_showing = False
            else:
                # Expand back surface
                self.change_card_image(self.back_surface, FLIP_SIZE_DELTA, -FLIP_X_DELTA)
                if self.image.relative_rect.width >= CARD_WIDTH:
                    self.flipped, self.flipping = False, False

    def move_card(self):
        """
        Iterative animation step for moving the card.

        Uses Linear Interpolation (lerp) to translate the card from
        start_location to target_location over MOVE_DURATION seconds.
        """

        self.move_time += self.scene.game.time_delta
        # Calculate progress (0.0 to 1.0)
        alpha = min(self.move_time / MOVE_DURATION, 1.0)

        # Calculate the intermediate position
        new_position = self.start_location.lerp(self.target_location, alpha)
        self.card_container.set_position(new_position)

        # Reset state once the destination is reached
        if alpha >= 1.0:
            self.moving = False
            self.start_location = pygame.Vector2(new_position)
            self.move_time = 0.0  # Reset timer for next movement
            if self.move_then_flip:
                self.move_then_flip = False
                self.flipping = True