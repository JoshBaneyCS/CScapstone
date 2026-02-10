# ----- Imports -----
import pygame
import pygame_gui

from scene import Scene, SceneID, TOP_LEFT
import credits

# ----- Globals/Constants -----
TITLE_SIZE = (900, 120)
TITLE_Y_LOCATION = 200
GAME_BUTTON_SIZE = (150, 50)
POKER_BUTTON_TEXT = 'Poker'
POKER_BUTTON_Y_LOCATION = 490
BLACKJACK_BUTTON_TEXT = 'Blackjack'
BLACKJACK_BUTTON_Y_LOCATION = 580
CREDITS_BUTTON_TEXT = 'Credits'
CREDITS_BUTTON_Y_LOCATION = 670

class GameMenu(Scene):
    """
    The main landing screen for the application.

    Provides navigation to different game modes (Poker, Blackjack) and
    displays an interactive credits roll.
    """
    def __init__(self, game):
        """
        Initializes the menu layout, buttons, and the hidden credits panel.

        Args:
            game: The main game engine instance.
        """
        Scene.__init__(self, game)

        # Placeholder for the dynamic text box created during the credits roll.
        self.text_box = pygame_gui.elements.UITextBox
        self.credit_roll_done = True

        # Main Game Title
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (self.center_x(TITLE_SIZE[0]), TITLE_Y_LOCATION),
                TITLE_SIZE),
            text=self.game.GAME_NAME,
            manager=self.ui_manager,
            container=self.scene_container,
            object_id='#title_label')

        # Navigation Buttons
        self.poker_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(GAME_BUTTON_SIZE[0]), POKER_BUTTON_Y_LOCATION),
                GAME_BUTTON_SIZE),
            text=POKER_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)
        self.blackjack_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(GAME_BUTTON_SIZE[0]), BLACKJACK_BUTTON_Y_LOCATION),
                GAME_BUTTON_SIZE),
            text=BLACKJACK_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)


        self.credits_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(GAME_BUTTON_SIZE[0]), CREDITS_BUTTON_Y_LOCATION),
                GAME_BUTTON_SIZE),
            text=CREDITS_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)

        # Credits Overlay Panel (Starts hidden and at a high z-depth)
        self.credits_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                (self.game.screen_width / 2 - self.game.GAME_RESOLUTION[0] / 2,
                 self.game.screen_height / 2 - self.game.GAME_RESOLUTION[1] / 2),
                self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            starting_height=100,
            visible=False,
            container=self.game.canvas,
            object_id='#credits_panel')

    def handle_events(self):
        """
        Manages user input for the menu.

        Handles scene transitions, credit triggering, and click-to-skip
        logic for the credits roll.
        """
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.poker_button:
                        self.game.change_scene(SceneID.POKER)
                    case self.blackjack_button:
                        self.game.change_scene(SceneID.BLACKJACK)
                    case self.credits_button:
                        self.play_credits()

            # Close or skip credits typing effect on mouse click
            if event.type == pygame.MOUSEBUTTONDOWN and self.credits_panel.visible:
                if event.button == 1:
                    self.handle_credit_text()

            # Detect when the typewriter effect for credits finishes
            if event.type == pygame_gui.UI_TEXT_EFFECT_FINISHED:
                if event.effect_type == pygame_gui.TEXT_EFFECT_TYPING_APPEAR:
                    self.credit_roll_done = True

            self.ui_manager.process_events(event)

    def update_scene(self):
        """Updates menu-specific logic (currently static)."""
        return

    def draw_scene(self):
        """Standard draw call using the base Scene renderer."""
        Scene.draw_scene(self)

    def handle_credit_text(self):
        """
        Controls the credits state machine.

        If text is still typing, clicking skips to the end.
        If text is finished, clicking closes the credits panel.
        """
        if self.text_box.visible and not self.credit_roll_done:
            self.text_box.set_active_effect(None)
            self.credit_roll_done = True
        elif self.text_box.visible and self.credit_roll_done:
            self.credits_panel.disable()
            self.credits_panel.hide()
            self.credit_roll_done = False

    def play_credits(self):
        """
        Populates and displays the credits panel with a typewriter effect.

        Joins credit strings with HTML breaks for display in the UITextBox.
        """
        self.credit_roll_done = False
        scrolling_text = "<br>".join(credits.CREDITS_STRINGS)

        self.credits_panel.enable()
        self.credits_panel.show()

        # Create the text box dynamically to ensure it starts the effect from the beginning
        self.text_box = pygame_gui.elements.UITextBox(
            html_text=scrolling_text,
            relative_rect=pygame.Rect(
                TOP_LEFT,
                self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            container=self.credits_panel,
            object_id="#credits_text_box"
        )

        # Apply the typewriter appearance effect
        self.text_box.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)