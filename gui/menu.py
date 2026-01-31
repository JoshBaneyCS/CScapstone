"""
Each scene represents the UI display for a specific part of the game:
    Logging in, selecting a game, and each games needs their own scene
TODO:
    - connect login to user authentication and add warning panel that is displayed on failure
    - add actual settings controls or change settings menu to logout/confirmation instead
    - add blackjack & poker scenes
    - add ids to each element for use with themes
"""
from enum import Enum
import pygame
import pygame_gui

## Used by game to call upon specific scenes
class SceneID(Enum):
    LOGIN_SCREEN = 1
    GAME_MENU = 2

## Base display that contains all the functionality shared by each screen
## Every scene has a settings menu
class Scene:
    def __init__(self, game):
        self.game = game
        self.ui_manager = pygame_gui.UIManager(self.game.GAME_RESOLUTION)
        self.run_display = True
        ## TODO: reference, can delete once themes are implemented
        ##self.background = pygame.Surface(self.game.GAME_RESOLUTION)
        ##self.background.fill(self.game.BACKGROUND_COLOR_DARK)

        ## Parent container for all UI Elements in this scene
        self.scene_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            starting_height=0)
        self.scene_container.disable()
        self.scene_container.hide()

        ## Settings button will be available in all scenes
        ## TODO: replace text with gear icon, change background alpha to 0
        self.settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((1850, 50), (50, 50)),
            text='Settings',
            manager=self.ui_manager,
            container=self.scene_container)
        self.settings_menu = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 200, self.game.GAME_HALF_HEIGHT - 200), (400, 400)),
            manager=self.ui_manager,
            container=self.scene_container,
            starting_height=100)
        self.logout_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((150, 225), (100, 50)),
            text='Logout',
            manager=self.ui_manager,
            container=self.settings_menu)
        self.return_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((150, 175), (100, 50)),
            text='Return',
            manager=self.ui_manager,
            container=self.settings_menu)

    def draw_scene(self):
        ##self.game.window.blit(self.background, (0,0))
        self.ui_manager.draw_ui(self.game.window)
        pygame.display.update()

    ## Ensure you call handle_settings_events when implement this in the subclass
    def handle_events(self):
        """
        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement 'method_to_implement'")

    def handle_settings_events(self, event):
        match event.ui_element:
            case self.settings_button:
                self.settings_menu.enable()
                self.settings_menu.show()
            case self.logout_button:
                self.game.change_scene(SceneID.LOGIN_SCREEN)
            case self.return_button:
                self.settings_menu.disable()
                self.settings_menu.hide()

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def open_scene(self):
        self.scene_container.enable()
        self.scene_container.show()
        self.settings_menu.disable()
        self.settings_menu.hide()

    def close_scene(self):
        self.scene_container.disable()
        self.scene_container.hide()

## Displays title and inputs for username and password
## Will change to the game selection screen upon successful login
## TODO: connect events to user authentication
class LoginScreen(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        self.menu_background = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 250, self.game.GAME_HALF_HEIGHT - 200), (500, 400)),
            manager=self.ui_manager,
            starting_height=0)
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 75, 200), (150, 50)),
            text=self.game.GAME_NAME,
            manager=self.ui_manager,
            container=self.scene_container)
        self.login_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 100, 350), (200, 50)),
            text='Please login to continue',
            manager=self.ui_manager,
            container=self.scene_container)
        self.username_textbox = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 50, 400), (100, 50)),
            initial_text="Username",
            manager=self.ui_manager,
            container=self.scene_container)
        self.password_textbox = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 50, 500), (100, 50)),
            initial_text="Password",
            manager=self.ui_manager,
            container=self.scene_container)
        self.login_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 75, 600), (150, 50)),
            text='Login',
            manager=self.ui_manager,
            container=self.scene_container)
        self.register_link = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 200, 650), (400, 50)),
            text='Don\'t have an account? Click here to create one!',
            manager=self.ui_manager,
            object_id="#register_link",
            container=self.scene_container)
        ## TODO: Debug button to close the application during testing
        self.exit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 50, 800), (100, 100)),
            text='Exit',
            manager=self.ui_manager,
            container=self.scene_container)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.is_running, self.game.is_playing = False, False
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.settings_button:
                        self.settings_menu.enable()
                        self.settings_menu.show()
                    case self.logout_button:
                        self.game.change_scene(SceneID.LOGIN_SCREEN)
                    case self.return_button:
                        self.settings_menu.disable()
                        self.settings_menu.hide()
                    case self.exit_button:
                        self.game.is_running, self.game.is_playing = False, False
                    case self.login_button:
                        self.game.change_scene(SceneID.GAME_MENU)
            self.ui_manager.process_events(event)

## Lets the user choose between all available casino card games
class GameMenu(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        ## TODO: Greet user with their name
        self.welcome_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 75, 200), (150, 50)),
            text="Welcome back!",
            manager=self.ui_manager,
            container=self.scene_container)
        self.poker_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 75, 490), (150, 50)),
            text='Poker',
            manager=self.ui_manager,
            container=self.scene_container)
        self.blackjack_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 75, 580), (150, 50)),
            text='Blackjack',
            manager=self.ui_manager,
            container=self.scene_container)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.is_running, self.game.is_playing = False, False
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.settings_button:
                        self.settings_menu.enable()
                        self.settings_menu.show()
                    case self.logout_button:
                        self.game.change_scene(SceneID.LOGIN_SCREEN)
                    case self.return_button:
                        self.settings_menu.disable()
                        self.settings_menu.hide()
                    ## TODO: swap to poker scene once implemented
                    case self.poker_button:
                        print("Play Poker!")
                    ## TODO: swap to blackjack scene once implemented
                    case self.blackjack_button:
                        print("Play Blackjack!")
            self.ui_manager.process_events(event)

## TODO: add scenes for poker/blackjack
