from enum import Enum
from card import Card
import pygame
import pygame_gui
from pygame_gui.core import ObjectID
import requests
import json

## Used by game to call upon specific scenes
class SceneID(Enum):
    LOGIN_SCREEN = 1
    GAME_MENU = 2
    BLACKJACK = 3
    POKER = 4

## Base display that contains all the functionality shared by each screen, including the settings menu
class Scene:
    def __init__(self, game):
        self.game = game
        self.ui_manager = pygame_gui.UIManager(self.game.GAME_RESOLUTION, "theme.json")
        self.run_display = True

        ## Parent container for all UI Elements in this scene
        ## Draw UI elements inside this container, not the main window
        self.scene_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((self.game.screen_width / 2 - self.game.GAME_RESOLUTION[0] / 2, self.game.screen_height / 2 - self.game.GAME_RESOLUTION[1] / 2), self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            starting_height=0,
            container=self.game.canvas,
            object_id=ObjectID(class_id='@screen_background'))
        self.scene_container.disable()
        self.scene_container.hide()

        ## Settings button is common to all scenes
        ## TODO: Add rules section to explain basic game rules
        self.settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((1850, 50), (50, 50)),
            text='',
            manager=self.ui_manager,
            container=self.scene_container,
            object_id='#settings_button')
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
        self.game.window.fill((0,0,0))
        self.ui_manager.draw_ui(self.game.window)
        pygame.display.update()

    ## Ensure you call handle_settings_events when implementing in subclass
    ## so that the settings button/menu will function
    def handle_events(self):
        """
        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement 'handle_events(self)'")

    def handle_settings_events(self, event):
        match event.ui_element:
            case self.settings_button:
                self.settings_menu.enable()
                self.settings_menu.show()
                return True
            case self.logout_button:
                self.game.change_scene(SceneID.LOGIN_SCREEN)
                return True
            case self.return_button:
                self.settings_menu.disable()
                self.settings_menu.hide()
                return True

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
## TODO: connect input to user authentication
## TODO: add a credits button/popup that will allow attribution for resources used and group member work
class LoginScreen(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        self.login_background = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 250, self.game.GAME_HALF_HEIGHT - 200), (500, 400)),
            manager=self.ui_manager,
            starting_height=0,
            container=self.scene_container,
            object_id=ObjectID(object_id='#login_background',class_id='@menu_background'))
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 450, 200), (900, 120)),
            text=self.game.GAME_NAME,
            manager=self.ui_manager,
            container=self.scene_container,
            object_id='#title_label')
        self.login_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 150, 325), (300, 100)),
            text='Please login to continue',
            manager=self.ui_manager,
            container=self.scene_container)
        self.username_textbox = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 50, 450), (100, 50)),
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
        ## NOTE: Debug button to close the application, delete before sending to prod
        ## User should not have ability to close the application. They exit by closing
        ## their browser/tab
        self.exit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 50, 800), (100, 100)),
            text='Exit',
            manager=self.ui_manager,
            container=self.scene_container)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if Scene.handle_settings_events(self, event):
                        pass
                else:
                    match event.ui_element:
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
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 100, 200), (200, 50)),
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
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if Scene.handle_settings_events(self, event):
                        pass
                else:
                    match event.ui_element:
                        case self.poker_button:
                            ## TODO: swap to poker scene
                            print("Play Poker!")
                        case self.blackjack_button:
                            self.game.change_scene(SceneID.BLACKJACK)
            self.ui_manager.process_events(event)

class BlackjackScene(Scene):
    ## TODO:
    # ----- Globals/Constants -----
    CARD_DECK_LOCATION = (1575, 130)
    PLAYER_CARD_LOCATION = (840, 360)
    DEALER_CARD_LOCATION = (840, 710)

    def __init__(self, game):
        Scene.__init__(self, game)
        self.place_bet_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((540 - 75, 540), (150, 50)),
            text='Place Bet',
            manager=self.ui_manager,
            container=self.scene_container)
        ## TODO: add text-box that enables user to place a custom bet amount
        self.hit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 225, 900), (150, 50)),
            text='Hit',
            manager=self.ui_manager,
            container=self.scene_container)
        self.stand_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH + 75, 900), (150, 50)),
            text='Stand',
            manager=self.ui_manager,
            container=self.scene_container)
        self.player_score = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.game.GAME_HALF_WIDTH - 25, 850), (50, 50)),
            text='0',
            manager=self.ui_manager,
            container=self.scene_container,
            object_id=ObjectID(object_id='#login_background'))
        ## TODO: add dealer score label

        self.deck = Card(self, self.CARD_DECK_LOCATION)
        self.player_cards = [ Card(self, self.CARD_DECK_LOCATION), Card(self, self.CARD_DECK_LOCATION) ]
        self.dealer_cards = [ Card(self, self.CARD_DECK_LOCATION), Card(self, self.CARD_DECK_LOCATION) ]

        self.blackjack_cards = self.player_cards.copy()
        self.blackjack_cards.append(self.deck)
        self.blackjack_cards.extend(self.dealer_cards)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if Scene.handle_settings_events(self, event):
                        pass
                else:
                    match event.ui_element:
                        case self.place_bet_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            payload = {'bet': '10'}
                            result = requests.post('http://172.18.0.2:8000/blackjack/start', data=json.dumps(payload))
                            print(result.text)
                        case self.hit_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            result = requests.post('http://172.18.0.2:8000/blackjack/hit')
                            print(result.text)
                        case self.stand_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            result = requests.post('http://172.18.0.2:8000/blackjack/stand')
                            print(result.text)
            self.ui_manager.process_events(event)

    def draw_scene(self):
        ## Called once per frame, but there should only be 4-10 cards to check
        # and only 1-2 will be flipping at a time
        for card in self.blackjack_cards:
            if card.flipping:
                card.flip_card()
        Scene.draw_scene(self)

## TODO: add scene(s) for poker