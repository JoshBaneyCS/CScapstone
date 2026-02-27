# ----- Imports -----
from enum import Enum
import json

import pygame
import pygame_gui
from pygame_gui.core import ObjectID

from api_client import api_get, api_post
from card import Card
from scene import (Scene, SceneID, WHITE_CHIP_WORTH, RED_CHIP_WORTH, GREEN_CHIP_WORTH,
                   BLUE_CHIP_WORTH, BLACK_CHIP_WORTH, MENU_BUTTON_TEXT, MENU_BUTTON_LOCATION,
                   MENU_BUTTON_SIZE)


class PokerGameState(Enum):
    """
    Represents the phases of a Poker hand (Texas Hold'em).
    Controls UI visibility for betting rounds and card animations.
    """
    SETUP = 0
    PRE_DEAL = 1
    STARTING_HOLE = 2
    DEALING_HOLE = 3
    HOLE_DEALT = 4
    HOLE_BETTING = 5
    STARTING_FLOP = 6
    DEALING_FLOP = 7
    FLOP_DEALT = 8
    FLOP_BETTING = 9
    STARTING_TURN = 10
    DEALING_TURN = 11
    TURN_DEALT = 12
    TURN_BETTING = 13
    STARTING_RIVER = 14
    DEALING_RIVER = 15
    RIVER_DEALT = 16
    RIVER_BETTING = 17
    SHOWDOWN = 18
    SHOWDOWN_FLIPPING = 19
    GAME_OVER = 20

# ----- Globals/Constants -----
# API calls
POKER_API_BASE = '/texas'
API_START = "single/start"
API_BET = "bet"
API_ACTION = "action"
API_FLOP = "flop"
API_TURN = "turn"
API_RIVER = "river"
API_SHOWDOWN = "showdown"
API_state = "state"

# ----- Globals/Constants -----
BUTTON_SIZE = (150, 50)
DEAL_BUTTON_TEXT = 'Deal'
DEAL_BUTTON_LOCATION = (400 - BUTTON_SIZE[0] / 2, 600)
RESET_BUTTON_TEXT = 'Reset'
RESET_BUTTON_LOCATION = (560 - BUTTON_SIZE[0] / 2, 600)

BET_AMOUNT_SIZE = (200, 55)
BET_AMOUNT_LOCATION = (200 - BET_AMOUNT_SIZE[0] / 2, 600)

STAY_BUTTON_LOCATION = (700, 900)
STAY_BUTTON_TEXT = 'Stay/Call'
RAISE_BUTTON_LOCATION = (900, 900)
RAISE_BUTTON_TEXT = 'Raise'
FOLD_BUTTON_LOCATION = (1100, 900)
FOLD_BUTTON_TEXT = 'Fold'

# Betting UI Layout
CHIP_CONTAINER_SIZE = (620, 420)
CHIP_CONTAINER_LOCATION = (50, 1080 - CHIP_CONTAINER_SIZE[1] - 10)
CHIP_SIZE = (200, 200)

# Local offsets within the chip container
WHITE_CHIP_LOCATION = (0, 0)
RED_CHIP_LOCATION = (200, 0)
GREEN_CHIP_LOCATION = (400, 0)
BLUE_CHIP_LOCATION = (100, 200)
BLACK_CHIP_LOCATION = (300, 200)

# Gameplay Animation Coordinates
CARD_START_LOCATION = (2000, -200) # Off-screen "Deck" location
PLAYER_LOCATION = (900, 650)
AI_CARD_LOCATIONS = [
    (1500, 150),  # Opponent 1
    (1500, 375),  # Opponent 2
    (1500, 600),  # Opponent 3
    (1500, 825)  # Opponent 4
]
AI_BET_LOCATIONS = [
    (1300, 150),  # Opponent 1
    (1300, 375),  # Opponent 2
    (1300, 600),  # Opponent 3
    (1300, 825)  # Opponent 4
]
AI_ACTION_LOCATIONS = [
    (1300, 225),  # Opponent 1
    (1300, 450),  # Opponent 2
    (1300, 675),  # Opponent 3
    (1300, 900)  # Opponent 4
]

BET_LABEL_SIZE = (150, 55)
POT_LABEL_SIZE = (150, 55)
POT_LABEL_LOCATION = (960 - POT_LABEL_SIZE[0], 540)

COMMUNITY_LOCATION = (700, 200)
CARD_HELD_OFFSET = 50 # Horizontal gap between cards in hand

BALANCE_LABEL_SIZE = (250, 55)
BALANCE_LABEL_LOCATION = (50, 50)
RESULT_LABEL_SIZE = (700, 500)
STARTING_BALANCE = 2500

class PokerScene(Scene):
    """
    Handles the logic and UI for the Poker game mode.

    Manages betting, card distribution, and the
    scoring state machine.
    """

    def __init__(self, game):
        """
        Initializes the poker table, UI components, and betting buttons.

        Args:
            game: The main game engine instance.
        """
        Scene.__init__(self, game)
        self.game_state = PokerGameState.SETUP
        self.bet_amount = WHITE_CHIP_WORTH
        #self.pot_amount = 0
        self.player_cards = []
        self.cpu1_cards = []
        #self.cpu1_bet = 0
        self.cpu2_cards = []
        #self.cpu2_bet = 0
        self.cpu3_cards = []
        #self.cpu3_bet = 0
        self.cpu4_cards = []
        #self.cpu4_bet = 0
        self.community_cards = []
        self.poker_cards = []
        self.current_status = ""
        self.game_data = None
        self.previous_game_data = self.game_data

        # Navigation
        self.menu_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(MENU_BUTTON_LOCATION, MENU_BUTTON_SIZE),
            text=MENU_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)

        # Game Control Buttons
        self.deal_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                DEAL_BUTTON_LOCATION,
                BUTTON_SIZE),
            text=DEAL_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)
        self.reset_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                RESET_BUTTON_LOCATION,
                BUTTON_SIZE),
            text=RESET_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)

        # Betting Display
        self.bet_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BET_AMOUNT_LOCATION,
                BET_AMOUNT_SIZE),
            text="$" + str(self.bet_amount),
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")

        # Chip Selection Panel
        self.chip_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                CHIP_CONTAINER_LOCATION,
                CHIP_CONTAINER_SIZE),
            manager=self.ui_manager,
            container=self.scene_container,
            starting_height=90,
            object_id=ObjectID(class_id='@popup_background'))

        # Individual Betting Chips
        self.white_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                WHITE_CHIP_LOCATION,
                CHIP_SIZE),
            text=str(WHITE_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#white_chip', class_id='@chip_button'))

        self.red_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                RED_CHIP_LOCATION,
                CHIP_SIZE),
            text=str(RED_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#red_chip', class_id='@chip_button'))

        self.green_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                GREEN_CHIP_LOCATION,
                CHIP_SIZE),
            text=str(GREEN_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#green_chip', class_id='@chip_button'))

        self.blue_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLUE_CHIP_LOCATION,
                CHIP_SIZE),
            text=str(BLUE_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#blue_chip', class_id='@chip_button'))

        self.black_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACK_CHIP_LOCATION,
                CHIP_SIZE),
            text=str(BLACK_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#black_chip', class_id='@chip_button'))

        self.balance = STARTING_BALANCE
        self.balance_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BALANCE_LABEL_LOCATION,
                BALANCE_LABEL_SIZE),
            text=f"${self.balance:.2f}",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.result_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (self.center_x(RESULT_LABEL_SIZE[0]), 300),
                RESULT_LABEL_SIZE),
            text="",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")

        self.stay_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                STAY_BUTTON_LOCATION,
                BUTTON_SIZE),
            text=STAY_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)
        self.raise_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                RAISE_BUTTON_LOCATION,
                BUTTON_SIZE),
            text=RAISE_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)
        self.fold_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                FOLD_BUTTON_LOCATION,
                BUTTON_SIZE),
            text=FOLD_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)

        # Money Displays
        self.pot_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                POT_LABEL_LOCATION,
                POT_LABEL_SIZE),
            text=f"$Pot: {0:.2f}",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.cpu1_bet_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                AI_BET_LOCATIONS[0],
                BET_LABEL_SIZE),
            text=f"${0:.2f}",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.cpu2_bet_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                AI_BET_LOCATIONS[1],
                BET_LABEL_SIZE),
            text=f"${0:.2f}",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.cpu3_bet_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                AI_BET_LOCATIONS[2],
                BET_LABEL_SIZE),
            text=f"${0:.2f}",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.cpu4_bet_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                AI_BET_LOCATIONS[3],
                BET_LABEL_SIZE),
            text=f"${0:.2f}",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")

        self.reset_board()

    def handle_events(self):
        """
        Processes Poker-specific input events.

        Handles betting increments via chip buttons, scene transitions,
        and triggers state changes for dealing, hitting, and standing.
        """
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.menu_button:
                        self.game.change_scene(SceneID.GAME_MENU)
                        return True
                    # Update bet amount and label based on chip value
                    case self.white_chip:
                        self.bet_amount = self.bet_amount + WHITE_CHIP_WORTH
                        self.bet_label.set_text("$" + str(self.bet_amount))
                    case self.red_chip:
                        self.bet_amount = self.bet_amount + RED_CHIP_WORTH
                        self.bet_label.set_text("$" + str(self.bet_amount))
                    case self.green_chip:
                        self.bet_amount = self.bet_amount + GREEN_CHIP_WORTH
                        self.bet_label.set_text("$" + str(self.bet_amount))
                    case self.blue_chip:
                        self.bet_amount = self.bet_amount + BLUE_CHIP_WORTH
                        self.bet_label.set_text("$" + str(self.bet_amount))
                    case self.black_chip:
                        self.bet_amount = self.bet_amount + BLACK_CHIP_WORTH
                        self.bet_label.set_text("$" + str(self.bet_amount))
                    case self.reset_button:
                        self.bet_amount = WHITE_CHIP_WORTH
                        self.bet_label.set_text("$" + str(self.bet_amount))
                    # Transition game states based on action buttons
                    case self.deal_button:
                        self.game_state = PokerGameState.STARTING_HOLE
                    case self.stay_button:
                        try:
                            data = api_get('/texas/state')
                        except Exception as e:
                            print(f"State API Error: {e}")
                            return

                        payload = {"action":"stay"}
                        try:
                            api_post('/texas/single/action', payload)
                        except Exception as e:
                            print(f"API Error: {e}")
                            return

                        if self.check_reraise():
                            continue


                        if self.game_state == PokerGameState.HOLE_BETTING:
                            self.game_state = PokerGameState.STARTING_FLOP
                        elif self.game_state == PokerGameState.FLOP_BETTING:
                            self.game_state = PokerGameState.STARTING_TURN
                        elif self.game_state == PokerGameState.TURN_BETTING:
                            self.game_state = PokerGameState.STARTING_RIVER
                        elif self.game_state == PokerGameState.RIVER_BETTING:
                            self.game_state = PokerGameState.SHOWDOWN
                    case self.raise_button:
                        payload = {"action":"raise", "amount": self.bet_amount}
                        try:
                            data = api_post('/texas/single/action', payload)
                        except Exception as e:
                            self.balance += self.bet_amount
                            self.balance_label.set_text(f"${self.balance:.2f}")
                            print(f"API Error: {e}")
                            return

                        if self.check_reraise():
                            continue

                        if self.game_state == PokerGameState.HOLE_BETTING:
                            self.game_state = PokerGameState.STARTING_FLOP
                        elif self.game_state == PokerGameState.FLOP_BETTING:
                            self.game_state = PokerGameState.STARTING_TURN
                        elif self.game_state == PokerGameState.TURN_BETTING:
                            self.game_state = PokerGameState.STARTING_RIVER
                        elif self.game_state == PokerGameState.RIVER_BETTING:
                            self.game_state = PokerGameState.SHOWDOWN
                    case self.fold_button:
                        payload = {"action":"fold"}
                        try:
                            data = api_post('/texas/single/action', payload)
                        except Exception as e:
                            print(f"API Error: {e}")
                            return

                        self.game_state = PokerGameState.GAME_OVER

            self.ui_manager.process_events(event)

    def draw_scene(self):
        """
        Renders the scene and executes per-frame card animations.

        Checks all cards in play; if a card is flagged as moving or flipping,
        it calls the respective animation update method.
        """
        for card in self.poker_cards:
            if card.moving:
                card.move_card()
            if card.flipping:
                card.flip_card()
        Scene.draw_scene(self)

    def update_scene(self):
        """
        The main state controller for the Poker game logic.

        Monitors the current PokerGameState and triggers logic or
        waits for animations to complete before transitioning to the next state.
        """
        if self.game_state == PokerGameState.SETUP:
            self.stay_button.disable()
            self.raise_button.disable()
            self.fold_button.disable()
            self.result_label.hide()
            self.game_state = PokerGameState.PRE_DEAL
        elif self.game_state == PokerGameState.PRE_DEAL:
            return
        elif self.game_state == PokerGameState.STARTING_HOLE:
            self.deal_poker()
        elif self.game_state == PokerGameState.DEALING_HOLE:
            for card in self.poker_cards:
                if card.moving or card.flipping:
                    return
            self.game_state = PokerGameState.HOLE_DEALT
        elif self.game_state == PokerGameState.HOLE_DEALT:
            self.bet_label.set_text("$" + str(WHITE_CHIP_WORTH))
            self.bet_amount = WHITE_CHIP_WORTH
            self.stay_button.enable()
            self.raise_button.enable()
            self.fold_button.enable()
            self.reset_button.enable()
            self.game_update()
            self.game_state = PokerGameState.HOLE_BETTING
        elif self.game_state == PokerGameState.HOLE_BETTING:
            return
        elif self.game_state == PokerGameState.STARTING_FLOP:
            self.deal_flop()
        elif self.game_state == PokerGameState.DEALING_FLOP:
            for card in self.poker_cards:
                if card.moving or card.flipping:
                    return
            self.game_state = PokerGameState.FLOP_DEALT
        elif self.game_state == PokerGameState.FLOP_DEALT:
            self.bet_label.set_text("$" + str(WHITE_CHIP_WORTH))
            self.bet_amount = WHITE_CHIP_WORTH
            self.stay_button.enable()
            self.raise_button.enable()
            self.fold_button.enable()
            self.reset_button.enable()
            self.game_update()
            self.game_state = PokerGameState.FLOP_BETTING
        elif self.game_state == PokerGameState.FLOP_BETTING:
            return
        elif self.game_state == PokerGameState.STARTING_TURN:
            self.deal_turn()
        elif self.game_state == PokerGameState.DEALING_TURN:
            for card in self.poker_cards:
                if card.moving or card.flipping:
                    return
            self.game_state = PokerGameState.TURN_DEALT
        elif self.game_state == PokerGameState.TURN_DEALT:
            self.bet_label.set_text("$" + str(WHITE_CHIP_WORTH))
            self.bet_amount = WHITE_CHIP_WORTH
            self.stay_button.enable()
            self.raise_button.enable()
            self.fold_button.enable()
            self.reset_button.enable()
            self.game_update()
            self.game_state = PokerGameState.TURN_BETTING
        elif self.game_state == PokerGameState.TURN_BETTING:
            return
        elif self.game_state == PokerGameState.STARTING_RIVER:
            self.deal_river()
        elif self.game_state == PokerGameState.DEALING_RIVER:
            for card in self.poker_cards:
                if card.moving or card.flipping:
                    return
            self.game_state = PokerGameState.RIVER_DEALT
        elif self.game_state == PokerGameState.RIVER_DEALT:
            self.bet_label.set_text("$" + str(WHITE_CHIP_WORTH))
            self.bet_amount = WHITE_CHIP_WORTH
            self.stay_button.enable()
            self.raise_button.enable()
            self.fold_button.enable()
            self.reset_button.enable()
            self.game_update()
            self.game_state = PokerGameState.RIVER_BETTING
        elif self.game_state == PokerGameState.RIVER_BETTING:
            return
        elif self.game_state == PokerGameState.SHOWDOWN:
            self.pot_label.set_text("test")
            self.show_cards()
        elif self.game_state == PokerGameState.SHOWDOWN_FLIPPING:
            for card in self.poker_cards:
                if card.moving or card.flipping:
                    return
            self.game_state = PokerGameState.GAME_OVER
        elif self.game_state == PokerGameState.GAME_OVER:
            self.finish_game()

    def reset_board(self):
        """
        Clears the current table and re-initializes player and dealer hand objects.
        """

        for card in self.poker_cards:
            card.image.kill()

        self.player_cards = [
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION) ]
        self.cpu1_cards = [
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION) ]
        self.cpu2_cards = [
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION) ]
        self.cpu3_cards = [
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION) ]
        self.cpu4_cards = [
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION) ]
        self.community_cards = [
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION),
            Card(self, CARD_START_LOCATION) ]

        # Master list used for animation loops in draw_scene
        self.poker_cards = self.player_cards.copy()
        self.poker_cards.extend(self.cpu1_cards)
        self.poker_cards.extend(self.cpu2_cards)
        self.poker_cards.extend(self.cpu3_cards)
        self.poker_cards.extend(self.cpu4_cards)
        self.poker_cards.extend(self.community_cards)
        self.result_label.hide()

        self.pot_label.set_text(f"${0:.2f}")
        self.cpu1_bet_label.set_text(f"${0:.2f}")
        self.cpu2_bet_label.set_text(f"${0:.2f}")
        self.cpu3_bet_label.set_text(f"${0:.2f}")
        self.cpu4_bet_label.set_text(f"${0:.2f}")

    def deal_poker(self):
        """
        Initiates a new round by contacting the Poker API.

        Disables betting UI, retrieves hand data, sets card faces,
        and triggers movement animations for the initial four cards.
        """
        self.reset_board()
        self.deal_button.disable()
        self.reset_button.disable()

        # Communication with the poker API
        payload = {"bet": str(self.bet_amount)}
        try:
            data = api_post('/texas/single/start', payload)
        except Exception as e:
            self.balance += self.bet_amount
            self.balance_label.set_text(f"${self.balance:.2f}")
            print(f"API Error: {e}")
            return

        self.game_data = data
        self.previous_game_data = self.game_data

        self.balance -= self.bet_amount
        self.balance_label.set_text(f"${self.balance:.2f}")

        # Setup Player Cards
        all_hands = data.get("players_hands")
        self.player_cards[0].set_front(all_hands.get("Player")[0])
        self.player_cards[1].set_front(all_hands.get("Player")[1])
        self.player_cards[0].target_location = pygame.Vector2(PLAYER_LOCATION)
        self.player_cards[1].target_location = pygame.Vector2(
            PLAYER_LOCATION[0] + 50, PLAYER_LOCATION[1])

        self.player_cards[0].moving = True
        self.player_cards[1].moving = True
        self.player_cards[0].move_then_flip = True
        self.player_cards[1].move_then_flip = True

        # Setup CPU cards
        self.cpu1_cards[0].set_front(all_hands.get("CPU1")[0])
        self.cpu1_cards[1].set_front(all_hands.get("CPU1")[1])
        self.cpu1_cards[0].target_location = pygame.Vector2(AI_CARD_LOCATIONS[0])
        self.cpu1_cards[1].target_location = pygame.Vector2(
            AI_CARD_LOCATIONS[0][0] + 50, AI_CARD_LOCATIONS[0][1])
        self.cpu1_cards[0].moving = True
        self.cpu1_cards[1].moving = True

        self.cpu2_cards[0].set_front(all_hands.get("CPU2")[0])
        self.cpu2_cards[1].set_front(all_hands.get("CPU2")[1])
        self.cpu2_cards[0].target_location = pygame.Vector2(AI_CARD_LOCATIONS[1])
        self.cpu2_cards[1].target_location = pygame.Vector2(
            AI_CARD_LOCATIONS[1][0] + 50, AI_CARD_LOCATIONS[1][1])
        self.cpu2_cards[0].moving = True
        self.cpu2_cards[1].moving = True

        self.cpu3_cards[0].set_front(all_hands.get("CPU3")[0])
        self.cpu3_cards[1].set_front(all_hands.get("CPU3")[1])
        self.cpu3_cards[0].target_location = pygame.Vector2(AI_CARD_LOCATIONS[2])
        self.cpu3_cards[1].target_location = pygame.Vector2(
            AI_CARD_LOCATIONS[2][0] + 50, AI_CARD_LOCATIONS[2][1])
        self.cpu3_cards[0].moving = True
        self.cpu3_cards[1].moving = True

        self.cpu4_cards[0].set_front(all_hands.get("CPU4")[0])
        self.cpu4_cards[1].set_front(all_hands.get("CPU4")[1])
        self.cpu4_cards[0].target_location = pygame.Vector2(AI_CARD_LOCATIONS[3])
        self.cpu4_cards[1].target_location = pygame.Vector2(
            AI_CARD_LOCATIONS[3][0] + 50, AI_CARD_LOCATIONS[3][1])
        self.cpu4_cards[0].moving = True
        self.cpu4_cards[1].moving = True

        self.game_state = PokerGameState.DEALING_HOLE

    def deal_flop(self):
        self.stay_button.disable()
        self.raise_button.disable()
        self.fold_button.disable()
        self.reset_button.disable()

        try:
            data = api_get('/texas/state')
        except Exception as e:
            print(f"State API Error: {e}")
            return

        community_cards_data = data.get("community_cards")
        self.community_cards[0].set_front(community_cards_data[0])
        self.community_cards[1].set_front(community_cards_data[1])
        self.community_cards[2].set_front(community_cards_data[2])

        self.community_cards[0].target_location = pygame.Vector2(COMMUNITY_LOCATION)
        self.community_cards[1].target_location = pygame.Vector2(
            COMMUNITY_LOCATION[0] + 50, COMMUNITY_LOCATION[1])
        self.community_cards[2].target_location = pygame.Vector2(
            COMMUNITY_LOCATION[0] + 100, COMMUNITY_LOCATION[1])

        self.community_cards[0].moving = True
        self.community_cards[1].moving = True
        self.community_cards[2].moving = True
        self.community_cards[0].move_then_flip = True
        self.community_cards[1].move_then_flip = True
        self.community_cards[2].move_then_flip = True

        self.game_state = PokerGameState.DEALING_FLOP

    def deal_turn(self):
        self.stay_button.disable()
        self.raise_button.disable()
        self.fold_button.disable()
        self.reset_button.disable()

        try:
            data = api_get('/texas/state')
        except Exception as e:
            print(f"State API Error: {e}")
            return

        community_cards_data = data.get("community_cards")
        self.community_cards[3].set_front(community_cards_data[3])
        self.community_cards[3].target_location = pygame.Vector2(
            COMMUNITY_LOCATION[0] + 150, COMMUNITY_LOCATION[1])

        self.community_cards[3].moving = True
        self.community_cards[3].move_then_flip = True

        self.game_state = PokerGameState.DEALING_TURN

    def deal_river(self):
        self.stay_button.disable()
        self.raise_button.disable()
        self.fold_button.disable()
        self.reset_button.disable()

        try:
            data = api_get('/texas/state')
        except Exception as e:
            print(f"State API Error: {e}")
            return


        community_cards_data = data.get("community_cards")
        self.community_cards[4].set_front(community_cards_data[4])
        self.community_cards[4].target_location = pygame.Vector2(
            COMMUNITY_LOCATION[0] + 200, COMMUNITY_LOCATION[1])

        self.community_cards[4].moving = True
        self.community_cards[4].move_then_flip = True

        self.game_state = PokerGameState.DEALING_RIVER

    def show_cards(self):
        self.stay_button.disable()
        self.raise_button.disable()
        self.fold_button.disable()
        self.reset_button.disable()

        self.cpu1_cards[0].flipping = True
        self.cpu1_cards[1].flipping = True
        self.cpu2_cards[0].flipping = True
        self.cpu2_cards[1].flipping = True
        self.cpu3_cards[0].flipping = True
        self.cpu3_cards[1].flipping = True
        self.cpu4_cards[0].flipping = True
        self.cpu4_cards[1].flipping = True

        self.game_state = PokerGameState.SHOWDOWN_FLIPPING

    def game_update(self):
        try:
            data = api_get('/texas/state')
        except Exception as e:
            print(f"State API Error: {e}")
            return

        self.previous_game_data = self.game_data
        self.game_data = data

        pot_amount = data["pot"]
        self.pot_label.set_text(f"${pot_amount:.2f}")

        round_bets = data.get("round_bets")
        last_actions = data.get("last_action")

        if last_actions.get("CPU1") == "fold":
            self.cpu1_bet_label.set_text("Fold")
        else:
            cpu1_bet = round_bets.get("CPU1")
            self.cpu1_bet_label.set_text(f"${cpu1_bet:.2f}")

        if last_actions.get("CPU2") == "fold":
            self.cpu2_bet_label.set_text("Fold")
        else:
            cpu2_bet = round_bets.get("CPU2")
            self.cpu2_bet_label.set_text(f"${cpu2_bet:.2f}")

        if last_actions.get("CPU3") == "fold":
            self.cpu3_bet_label.set_text("Fold")
        else:
            cpu3_bet = round_bets.get("CPU3")
            self.cpu3_bet_label.set_text(f"${cpu3_bet:.2f}")

        if last_actions.get("CPU4") == "fold":
            self.cpu4_bet_label.set_text("Fold")
        else:
            cpu4_bet = round_bets.get("CPU4")
            self.cpu4_bet_label.set_text(f"${cpu4_bet:.2f}")

        if data["status"] == "finished":
            self.game_state = PokerGameState.GAME_OVER

        self.current_status = data["status"]

    def check_reraise(self):
        try:
            data = api_get('/texas/state')
        except Exception as e:
            print(f"State API Error: {e}")
            return

        #self.previous_game_data = self.game_data
        #self.game_data = data

        round_bets = data.get("round_bets")
        last_actions = data.get("last_action")
        old_actions = self.previous_game_data.get("last_action")

        if data["status"] == self.current_status:

            if last_actions.get("CPU1") == "fold":
                self.cpu1_bet_label.set_text("Fold")
            elif last_actions.get("CPU1") == "raise" and old_actions.get("CPU1") != "raise":
                cpu1_bet = round_bets.get("CPU1")
                self.cpu1_bet_label.set_text(f"${cpu1_bet:.2f}")
                pot_amount = data["pot"]
                self.pot_label.set_text(f"${pot_amount:.2f}")

            if last_actions.get("CPU2") == "fold":
                self.cpu2_bet_label.set_text("Fold")
            elif last_actions.get("CPU2") == "raise" and old_actions.get("CPU2") != "raise":
                cpu2_bet = round_bets.get("CPU2")
                self.cpu2_bet_label.set_text(f"${cpu2_bet:.2f}")
                pot_amount = data["pot"]
                self.pot_label.set_text(f"${pot_amount:.2f}")
            if last_actions.get("CPU3") == "fold":
                self.cpu3_bet_label.set_text("Fold")
            elif last_actions.get("CPU3") == "raise" and old_actions.get("CPU3") != "raise":
                cpu3_bet = round_bets.get("CPU3")
                self.cpu3_bet_label.set_text(f"${cpu3_bet:.2f}")
                pot_amount = data["pot"]
                self.pot_label.set_text(f"${pot_amount:.2f}")

            if last_actions.get("CPU4") == "fold":
                self.cpu4_bet_label.set_text("Fold")
            elif last_actions.get("CPU4") == "raise" and old_actions.get("CPU4") != "raise":
                cpu4_bet = round_bets.get("CPU4")
                self.cpu4_bet_label.set_text(f"${cpu4_bet:.2f}")
                pot_amount = data["pot"]
                self.pot_label.set_text(f"${pot_amount:.2f}")


        if data["status"] == "finished":
            self.current_status = data["status"]
            self.game_state = PokerGameState.GAME_OVER
            return False
        elif ((last_actions.get("CPU1") == "raise" and  old_actions.get("CPU1") != "raise") or
              (last_actions.get("CPU2") == "raise"  and old_actions.get("CPU2") != "raise") or
              (last_actions.get("CPU3") == "raise"  and old_actions.get("CPU3") != "raise") or
              (last_actions.get("CPU4") == "raise" and old_actions.get("CPU4") != "raise" )):
            self.current_status = data["status"]
            return True
        else:
            return False

    def finish_game(self):
        self.result_label.set_text("Finished!")
        self.result_label.show()

        self.stay_button.disable()
        self.raise_button.disable()
        self.fold_button.disable()
        self.deal_button.enable()
        self.reset_button.enable()
        self.game_state = PokerGameState.PRE_DEAL
