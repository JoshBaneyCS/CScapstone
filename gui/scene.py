from enum import Enum
import pygame
import pygame_gui
from pygame_gui.core import ObjectID
import requests
import json
from card import Card

## Used by game to call upon specific scenes
class SceneID(Enum):
    GAME_MENU = 1
    BLACKJACK = 2
    POKER = 3

# ----- Globals/Constants -----
BLACK = (0,0,0)

## Scene
SETTINGS_BUTTON_SIZE = (50, 50)
SETTINGS_BUTTON_LOCATION = (1850 - SETTINGS_BUTTON_SIZE[0] / 2, 50)
SETTINGS_PANEL_SIZE = (400, 400)
SETTINGS_BUTTON_SIZE = (100, 50)
SETTINGS_LEAVE_BUTTON_LOCATION = (
    200 - SETTINGS_BUTTON_SIZE[0] / 2,
    100 - SETTINGS_BUTTON_SIZE[1] / 2)
SETTINGS_CLOSE_BUTTON_LOCATION = (
    200 - SETTINGS_BUTTON_SIZE[0] / 2 ,
    200 - SETTINGS_BUTTON_SIZE[1] / 2 )

## Game Menu
TITLE_SIZE = (900, 120)
TITLE_Y_LOCATION = 200
GAME_BUTTON_SIZE = (150, 50)
POKER_BUTTON_Y_LOCATION = 490
BLACKJACK_BUTTON_Y_LOCATION = 580

## Blackjack
BLACKJACK_BUTTON_SIZE = (150, 50)
BLACKJACK_HIT_BUTTON_X_DELTA = 225
BLACKJACK_STAND_BUTTON_X_DELTA = -75
BLACKJACK_ACTION_BUTTON_Y = 900
BET_BUTTON_LOCATION = (540 - BLACKJACK_BUTTON_SIZE[0] / 2, 540)
BLACKJACK_PLAYER_SCORE_SIZE = (50, 50)
BLACKJACK_PLAYER_SCORE_Y = 850
BLACKJACK_DECK_LOCATION = (1575, 130)
BLACKJACK_PLAYER_LOCATION = (840, 360)
BLACKJACK_DEALER_LOCATION = (840, 710)

## Poker
POKER_DECK_LOCATION = (1575, 130)
POKER_PLAYER_LOCATION = (840, 360)
POKER_AI_LOCATION = (840, 710)

## Base display that contains all the functionality shared by each screen, including the settings menu
class Scene:
    def __init__(self, game):
        self.game = game
        self.ui_manager = pygame_gui.UIManager(self.game.GAME_RESOLUTION, "theme.json")
        self.run_display = True

        ## Parent container for all UI Elements in this scene
        ## Draw UI elements inside this container, not the main window
        self.scene_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                (self.game.screen_width / 2 - self.game.GAME_RESOLUTION[0] / 2,
                 self.game.screen_height / 2 - self.game.GAME_RESOLUTION[1] / 2),
                self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            starting_height=0,
            container=self.game.canvas,
            object_id=ObjectID(class_id='@screen_background'))
        self.scene_container.disable()
        self.scene_container.hide()

        ## Settings button is common to all scenes
        ## TODO: Add rules section to explain basic game rules
        self.settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(SETTINGS_BUTTON_LOCATION, SETTINGS_BUTTON_SIZE),
            text='',
            manager=self.ui_manager,
            container=self.scene_container,
            object_id='#settings_button')
        self.settings_menu = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((
                self.game.GAME_HALF_WIDTH - SETTINGS_PANEL_SIZE[0] / 2,
                self.game.GAME_HALF_HEIGHT - SETTINGS_PANEL_SIZE[1] / 2),
                SETTINGS_PANEL_SIZE),
            manager=self.ui_manager,
            container=self.scene_container,
            starting_height=100,
            object_id='#settings_menu')
        self.leave_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(SETTINGS_LEAVE_BUTTON_LOCATION, SETTINGS_BUTTON_SIZE),
            text='Leave',
            manager=self.ui_manager,
            container=self.settings_menu)
        self.close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(SETTINGS_CLOSE_BUTTON_LOCATION, SETTINGS_BUTTON_SIZE),
            text='Close',
            manager=self.ui_manager,
            container=self.settings_menu)

    def draw_scene(self):
        self.game.window.fill(BLACK)
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
            case self.leave_button:
                self.settings_menu.disable()
                self.settings_menu.hide()
                self.game.change_scene(SceneID.GAME_MENU)
                return True
            case self.close_button:
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

    ## returns centered x location based the elements width
    def center_x(self, width):
        return self.game.GAME_HALF_WIDTH - (width / 2)

    ## returns centered y location based the elements height
    def center_y(self, height):
        return self.game.GAME_HALF_HEIGHT - (height / 2)

## Lets the user choose between all available casino card games
class GameMenu(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        ## TODO: Greet user with their name
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (self.center_x(TITLE_SIZE[0]), TITLE_Y_LOCATION),
                TITLE_SIZE),
            text=self.game.GAME_NAME,
            manager=self.ui_manager,
            container=self.scene_container,
            object_id='#title_label')
        self.poker_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(GAME_BUTTON_SIZE[0]), POKER_BUTTON_Y_LOCATION),
                GAME_BUTTON_SIZE),
            text='Poker',
            manager=self.ui_manager,
            container=self.scene_container)
        self.blackjack_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(GAME_BUTTON_SIZE[0]), BLACKJACK_BUTTON_Y_LOCATION),
                GAME_BUTTON_SIZE),
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
                            self.game.change_scene(SceneID.POKER)
                        case self.blackjack_button:
                            self.game.change_scene(SceneID.BLACKJACK)
            self.ui_manager.process_events(event)

class BlackjackScene(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        self.place_bet_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BET_BUTTON_LOCATION,
                BLACKJACK_BUTTON_SIZE),
            text='Place Bet',
            manager=self.ui_manager,
            container=self.scene_container)
        ## TODO: add text-box that enables user to place a custom bet amount
        self.hit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(BLACKJACK_HIT_BUTTON_X_DELTA), BLACKJACK_ACTION_BUTTON_Y),
                BLACKJACK_BUTTON_SIZE),
            text='Hit',
            manager=self.ui_manager,
            container=self.scene_container)
        self.stand_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(BLACKJACK_STAND_BUTTON_X_DELTA), BLACKJACK_ACTION_BUTTON_Y),
                BLACKJACK_BUTTON_SIZE),
            text='Stand',
            manager=self.ui_manager,
            container=self.scene_container)
        self.player_score = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (self.center_x(-BLACKJACK_PLAYER_SCORE_SIZE[0]), BLACKJACK_PLAYER_SCORE_Y),
                BLACKJACK_PLAYER_SCORE_SIZE),
            text='0',
            manager=self.ui_manager,
            container=self.scene_container)
        ## TODO: add dealer score label

        self.deck = Card(self, BLACKJACK_DECK_LOCATION)
        self.player_cards = [ Card(self, BLACKJACK_DECK_LOCATION), Card(self, BLACKJACK_DECK_LOCATION) ]
        self.dealer_cards = [ Card(self, BLACKJACK_DECK_LOCATION), Card(self, BLACKJACK_DECK_LOCATION) ]

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
                            result = requests.post('http://blackjack-api:8000/blackjack/start', data=json.dumps(payload))
                            print(result.text)
                        case self.hit_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            result = requests.post('http://blackjack-api:8000/blackjack/hit')
                            print(result.text)
                        case self.stand_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            result = requests.post('http://blackjack-api:8000/blackjack/stand')
                            print(result.text)
            self.ui_manager.process_events(event)

    def draw_scene(self):
        ## Called once per frame, but there should only be 4-10 cards to check
        # and only 1-2 will be flipping at a time
        for card in self.blackjack_cards:
            if card.flipping:
                card.flip_card()
        Scene.draw_scene(self)

class PokerScene(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        """
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
        """
        ## TODO: alot

        self.deck = Card(self, POKER_DECK_LOCATION)
        self.player_cards = [ Card(self, POKER_DECK_LOCATION), Card(self, POKER_DECK_LOCATION) ]
        self.ai_cards = [ Card(self, POKER_DECK_LOCATION), Card(self, POKER_DECK_LOCATION) ]

        self.poker_cards = self.player_cards.copy()
        self.poker_cards.append(self.deck)
        self.poker_cards.extend(self.ai_cards)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if Scene.handle_settings_events(self, event):
                        pass
                """
                else:
                    match event.ui_element:
                        ## TODO: base functionality for poker unverified and probably wrong
                        case self.place_bet_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            payload = {'bet': '10'}
                            result = requests.post('http://poker-api:8001/texas/old_start', data=json.dumps(payload))
                            print(result.text)
                        case self.hit_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            result = requests.post('http://poker-api:8000/texas/single/bet')
                            print(result.text)
                        case self.stand_button:
                            ## TODO: Base functionality verification, use as a template to build full functionality
                            result = requests.post('http://poker-api:8000/blackjack/state')
                            print(result.text)
                """
            self.ui_manager.process_events(event)

    def draw_scene(self):
        ## Called once per frame, but there should only be 4-10 cards to check
        # and only 1-2 will be flipping at a time
        for card in self.poker_cards:
            if card.flipping:
                card.flip_card()
        Scene.draw_scene(self)

