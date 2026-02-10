# ----- Imports -----
from enum import Enum
import requests
import json

import pygame
import pygame_gui
from pygame_gui.core import ObjectID

from card import Card
from scene import (Scene, SceneID, WHITE_CHIP_WORTH, RED_CHIP_WORTH, GREEN_CHIP_WORTH,
                   BLUE_CHIP_WORTH, BLACK_CHIP_WORTH, MENU_BUTTON_TEXT, MENU_BUTTON_LOCATION,
                   MENU_BUTTON_SIZE)

class BlackjackGameState(Enum):
    """
    Represents the various phases of a Blackjack game round.
    Used to control UI visibility and game logic flow in the update loop.
    """
    SETUP = 0               # Initial scene loading
    PRE_DEAL = 1            # Waiting for player to place bets
    START_DEAL = 2          # Beginning the physical card movement
    DEALING = 3             # Animation state for cards moving to table
    DEALT = 4               # Cards are on table, checking for naturals
    PLAYER_TURN = 5         # Waiting for player input (Hit/Stand)
    GIVE_PLAYER_CARD = 6    # Requesting a new card for the player
    WAITING_PLAYER_CARD = 7 # Animation delay for player's hit card
    RESOLVING_HIT = 8       # Checking if player busted or can hit again
    PLAYER_STANDS = 9       # Transition to dealer's turn
    DEALER_FLIPS = 10       # Reveal dealer's hidden card
    WAITING_DEALER_CARD = 11# Animation delay for dealer's hit card
    DEALER_TURN = 12        # Dealer AI logic (hit until 17)
    GAME_OVER = 13          # Results displayed, waiting for reset

# ----- Globals/Constants -----
BLACKJACK_BUTTON_SIZE = (150, 50)
BLACKJACK_HIT_BUTTON_TEXT = 'Hit'
BLACKJACK_HIT_BUTTON_X_DELTA = 400
BLACKJACK_STAND_BUTTON_TEXT = 'Stand'
BLACKJACK_STAND_BUTTON_X_DELTA = -400
BLACKJACK_ACTION_BUTTON_Y = 540

BLACKJACK_BET_AMOUNT_SIZE = (200, 55)
BLACKJACK_BET_AMOUNT_LOCATION = (200 - BLACKJACK_BET_AMOUNT_SIZE[0] / 2, 600)

BLACKJACK_DEAL_BUTTON_TEXT = 'Deal'
BLACKJACK_DEAL_BUTTON_LOCATION = (400 - BLACKJACK_BUTTON_SIZE[0] / 2, 600)
BLACKJACK_RESET_BUTTON_TEXT = 'Reset'
BLACKJACK_RESET_BUTTON_LOCATION = (560 - BLACKJACK_BUTTON_SIZE[0] / 2, 600)

# Betting UI Layout
BLACKJACK_CHIP_CONTAINER_SIZE = (620, 420)
BLACKJACK_CHIP_CONTAINER_LOCATION = (50, 1080 - BLACKJACK_CHIP_CONTAINER_SIZE[1] - 10)
BLACKJACK_CHIP_SIZE = (200, 200)

# Local offsets within the chip container
BLACKJACK_WHITE_CHIP_LOCATION = (0, 0)
BLACKJACK_RED_CHIP_LOCATION = (200, 0)
BLACKJACK_GREEN_CHIP_LOCATION = (400, 0)
BLACKJACK_BLUE_CHIP_LOCATION = (100, 200)
BLACKJACK_BLACK_CHIP_LOCATION = (300, 200)

# Scoreboard Layout
BLACKJACK_SCORE_SIZE = (55, 55)
BLACKJACK_PLAYER_LABEL_TEXT = 'Player'
BLACKJACK_PLAYER_SCORE_LOCATION = (1400, 740)
BLACKJACK_SCORE_LABEL_SIZE = (150, 55)
BLACKJACK_PLAYER_SCORE_LABEL_LOCATION = (1500, 740)
BLACKJACK_DEALER_SCORE_LOCATION = (1400, 340)
BLACKJACK_DEALER_LABEL_TEXT = 'Dealer'
BLACKJACK_DEALER_SCORE_LABEL_LOCATION = (1500, 340)

# Gameplay Animation Coordinates
BLACKJACK_CARD_START_LOCATION = (2000, -200) # Off-screen "Deck" location
BLACKJACK_PLAYER_LOCATION = (900, 650)
BLACKJACK_DEALER_LOCATION = (900, 270)
BLACKJACK_CARD_HELD_OFFSET = 50 # Horizontal gap between cards in hand

class BlackjackScene(Scene):
    """
    Handles the logic and UI for the Blackjack game mode.

    Manages betting, card distribution, dealer AI, and the
    scoring state machine.
    """

    def __init__(self, game):
        """
        Initializes the blackjack table, UI components, and betting buttons.

        Args:
            game: The main game engine instance.
        """
        Scene.__init__(self, game)
        self.game_state = BlackjackGameState.SETUP
        self.bet_amount = WHITE_CHIP_WORTH
        self.player_cards = []
        self.blackjack_cards = []

        # Navigation
        self.menu_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(MENU_BUTTON_LOCATION, MENU_BUTTON_SIZE),
            text=MENU_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)

        # Game Control Buttons
        self.deal_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_DEAL_BUTTON_LOCATION,
                BLACKJACK_BUTTON_SIZE),
            text=BLACKJACK_DEAL_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)
        self.reset_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_RESET_BUTTON_LOCATION,
                BLACKJACK_BUTTON_SIZE),
            text=BLACKJACK_RESET_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)

        # Betting Display
        self.bet_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BLACKJACK_BET_AMOUNT_LOCATION,
                BLACKJACK_BET_AMOUNT_SIZE),
            text="$" + str(self.bet_amount),
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")

        # Chip Selection Panel
        self.chip_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                BLACKJACK_CHIP_CONTAINER_LOCATION,
                BLACKJACK_CHIP_CONTAINER_SIZE),
            manager=self.ui_manager,
            container=self.scene_container,
            starting_height=90,
            object_id=ObjectID(class_id='@popup_background'))

        # Individual Betting Chips
        self.white_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_WHITE_CHIP_LOCATION,
                BLACKJACK_CHIP_SIZE),
            text=str(WHITE_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#white_chip', class_id='@chip_button'))

        self.red_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_RED_CHIP_LOCATION,
                BLACKJACK_CHIP_SIZE),
            text=str(RED_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#red_chip', class_id='@chip_button'))

        self.green_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_GREEN_CHIP_LOCATION,
                BLACKJACK_CHIP_SIZE),
            text=str(GREEN_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#green_chip', class_id='@chip_button'))

        self.blue_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_BLUE_CHIP_LOCATION,
                BLACKJACK_CHIP_SIZE),
            text=str(BLUE_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#blue_chip', class_id='@chip_button'))

        self.black_chip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_BLACK_CHIP_LOCATION,
                BLACKJACK_CHIP_SIZE),
            text=str(BLACK_CHIP_WORTH),
            manager=self.ui_manager,
            container=self.chip_container,
        object_id = ObjectID(object_id='#black_chip', class_id='@chip_button'))

        # Gameplay Action Buttons (Hidden until Deal)
        self.hit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(BLACKJACK_HIT_BUTTON_X_DELTA), BLACKJACK_ACTION_BUTTON_Y),
                BLACKJACK_BUTTON_SIZE),
            text=BLACKJACK_HIT_BUTTON_TEXT,
            manager=self.ui_manager,
            visible=False,
            container=self.scene_container)

        self.stand_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(BLACKJACK_STAND_BUTTON_X_DELTA), BLACKJACK_ACTION_BUTTON_Y),
                BLACKJACK_BUTTON_SIZE),
            text=BLACKJACK_STAND_BUTTON_TEXT,
            manager=self.ui_manager,
            container=self.scene_container)

        # Player/Dealer Scoreboards
        self.player_score = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BLACKJACK_PLAYER_SCORE_LOCATION,
                BLACKJACK_SCORE_SIZE),
            text='0',
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="@blackjack_score")

        self.player_score_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BLACKJACK_PLAYER_SCORE_LABEL_LOCATION,
                BLACKJACK_SCORE_LABEL_SIZE),
            text=BLACKJACK_PLAYER_LABEL_TEXT,
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="@blackjack_score")

        self.dealer_score = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BLACKJACK_DEALER_SCORE_LOCATION,
                BLACKJACK_SCORE_SIZE),
            text='0',
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="@blackjack_score")

        self.dealer_score_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BLACKJACK_DEALER_SCORE_LABEL_LOCATION,
                BLACKJACK_SCORE_LABEL_SIZE),
            text=BLACKJACK_DEALER_LABEL_TEXT,
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="@blackjack_score")

        self.reset_board()

    def handle_events(self):
        """
        Processes Blackjack-specific input events.

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
                    # Transition game states based on action buttons
                    case self.deal_button:
                        self.game_state = BlackjackGameState.START_DEAL
                    case self.reset_button:
                        self.bet_amount = WHITE_CHIP_WORTH
                        self.bet_label = "$" + str(self.bet_amount)
                    case self.hit_button:
                        self.game_state = BlackjackGameState.GIVE_PLAYER_CARD
                    case self.stand_button:
                        self.game_state = BlackjackGameState.PLAYER_STANDS
            self.ui_manager.process_events(event)

    def draw_scene(self):
        """
        Renders the scene and executes per-frame card animations.

        Checks all cards in play; if a card is flagged as moving or flipping,
        it calls the respective animation update method.
        """
        for card in self.blackjack_cards:
            if card.moving:
                card.move_card()
            if card.flipping:
                card.flip_card()
        Scene.draw_scene(self)

    def update_scene(self):
        """
        The main state controller for the Blackjack game logic.

        Monitors the current BlackjackGameState and triggers logic or
        waits for animations to complete before transitioning to the next state.
        """
        match self.game_state:
            case BlackjackGameState.SETUP:
                self.hit_button.disable()
                self.stand_button.disable()
                self.player_score.hide()
                self.dealer_score.hide()
                self.game_state = BlackjackGameState.PRE_DEAL

            case BlackjackGameState.PRE_DEAL:
                # Waiting for player to finish betting and press 'Deal'
                return

            case BlackjackGameState.START_DEAL:
                self.deal_blackjack()

            case BlackjackGameState.DEALING:
                # Stall logic until all initial dealing animations finish
                for card in self.blackjack_cards:
                    if card.moving or card.flipping:
                        return
                self.game_state = BlackjackGameState.DEALT

            case BlackjackGameState.DEALT:
                self.hit_button.enable()
                self.stand_button.enable()
                self.player_score.show()
                self.dealer_score.show()
                self.game_state = BlackjackGameState.PLAYER_TURN

            case BlackjackGameState.PLAYER_TURN:
                return

            case BlackjackGameState.GIVE_PLAYER_CARD:
                self.give_player_card()

            case BlackjackGameState.WAITING_PLAYER_CARD:
                # Stall logic until the 'Hit' card animation finishes
                for card in self.player_cards:
                    if card.moving or card.flipping:
                        return
                self.game_state = BlackjackGameState.RESOLVING_HIT

            case BlackjackGameState.RESOLVING_HIT:
                self.resolve_hit()

            case BlackjackGameState.PLAYER_STANDS:
                self.player_stands()

            case BlackjackGameState.WAITING_DEALER_CARD:
                for card in self.dealer_cards:
                    if card.moving or card.flipping:
                        return
                self.game_state = BlackjackGameState.DEALER_TURN

            case BlackjackGameState.DEALER_TURN:
                self.dealer_turn()

    def reset_board(self):
        """
        Clears the current table and re-initializes player and dealer hand objects.
        """

        for card in self.blackjack_cards:
            card.image.kill()

        self.player_cards = [
            Card(self, BLACKJACK_CARD_START_LOCATION),
            Card(self, BLACKJACK_CARD_START_LOCATION) ]
        self.dealer_cards = [
            Card(self, BLACKJACK_CARD_START_LOCATION),
            Card(self, BLACKJACK_CARD_START_LOCATION) ]

        # Master list used for animation loops in draw_scene
        self.blackjack_cards = self.player_cards.copy()
        self.blackjack_cards.extend(self.dealer_cards)

        self.player_score.set_text("0")
        self.dealer_score.set_text("0")

    def deal_blackjack(self):
        """
        Initiates a new round by contacting the Blackjack API.

        Disables betting UI, retrieves hand data, sets card faces,
        and triggers movement animations for the initial four cards.
        """
        self.reset_board()
        self.deal_button.disable()
        self.reset_button.disable()
        self.chip_container.disable()

        # Communication with the local blackjack-api service
        payload = {'bet': str(self.bet_amount)}
        try:
            response = requests.post('http://blackjack-api:8000/blackjack/start', data=json.dumps(payload))
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return

        # Setup Player Cards
        self.player_cards[0].set_front(data["player_hand"][0])
        self.player_cards[1].set_front(data["player_hand"][1])
        self.player_cards[0].target_location = pygame.Vector2(BLACKJACK_PLAYER_LOCATION)
        self.player_cards[1].target_location = pygame.Vector2(
            BLACKJACK_PLAYER_LOCATION[0] + 50, BLACKJACK_PLAYER_LOCATION[1])

        # Setup Dealer Cards
        self.player_cards[0].moving = True
        self.player_cards[1].moving = True
        self.player_cards[0].move_then_flip = True
        self.player_cards[1].move_then_flip = True
        self.dealer_cards[0].set_front(data["dealer_hand"][0])
        self.dealer_cards[1].set_front(data["dealer_hand"][1])
        self.dealer_cards[0].target_location = pygame.Vector2(BLACKJACK_DEALER_LOCATION)
        self.dealer_cards[1].target_location = pygame.Vector2(
            BLACKJACK_DEALER_LOCATION[0] + 50, BLACKJACK_DEALER_LOCATION[1])

        # Trigger animations (Player cards flip, Dealer's second card remains face down)
        for card in self.player_cards:
            card.moving = True
            card.move_then_flip = True

        self.dealer_cards[0].moving = True
        self.dealer_cards[1].moving = True
        self.dealer_cards[1].move_then_flip = True # Dealer's 'hole' card usually stays face down

        self.player_score.set_text(str(data["player_total"]))
        self.dealer_score.set_text(str(data["dealer_total"]))

        self.check_for_blackjack()

    def check_for_blackjack(self):
        """Checks the API for immediate win conditions (Naturals) after the deal."""
        response = requests.get('http://blackjack-api:8000/blackjack/state')
        data = response.json()
        match data["status"]:
            case "dealer_win":
                self.end_game_early()
            case "player_win":
                self.end_game_early()
            case _:
                self.game_state = BlackjackGameState.DEALING

    def give_player_card(self):
        """
        Requests an additional card (Hit) for the player.

        Instantiates a new Card object, sets its destination based on current
        hand size, and begins the move/flip animation.
        """
        self.hit_button.disable()
        self.stand_button.disable()

        response = requests.post('http://blackjack-api:8000/blackjack/hit')
        data = response.json()

        new_card = Card(self, BLACKJACK_CARD_START_LOCATION)
        self.player_cards.append(new_card)
        self.blackjack_cards.append(self.player_cards[-1])

        self.player_cards[-1].set_front(data["player_hand"][-1])
        self.player_cards[-1].target_location = pygame.Vector2(
            BLACKJACK_PLAYER_LOCATION[0] + BLACKJACK_CARD_HELD_OFFSET * (len(self.player_cards) - 1),
            BLACKJACK_PLAYER_LOCATION[1])

        new_card.moving = True
        new_card.move_then_flip = True

        self.player_score.set_text(str(data["player_total"]))
        #self.game_state = BlackjackGameState.RESOLVING_HIT
        self.game_state = BlackjackGameState.WAITING_PLAYER_CARD

    def resolve_hit(self):
        """Checks if the player has busted or won after receiving a 'Hit' card."""
        response = requests.get('http://blackjack-api:8000/blackjack/state')
        data = response.json()
        match data["status"]:
            ## TODO: add game over animations to game_over gs
            case "player_bust":
                self.end_game_early()
            case "player_win":
                self.end_game_early()
            case "in_progress":
                self.hit_button.enable()
                self.stand_button.enable()
                self.game_state = BlackjackGameState.PLAYER_TURN

    def player_stands(self):
        """
        Finalizes the player's hand and initiates the dealer's reveal.

        Signals the API that the player is standing, then begins the
        visual reveal of the dealer's cards.
        """
        self.hit_button.disable()
        self.stand_button.disable()

        # Tell the API the player is done so it can process the dealer's hand.
        try:
            requests.post('http://blackjack-api:8000/blackjack/stand')
        except requests.exceptions.RequestException as e:
            print(f"Stand API Error: {e}")

        # Reveal the first dealer card (the one typically dealt face-down)
        self.dealer_cards[0].flipping = True
        self.game_state = BlackjackGameState.WAITING_DEALER_CARD

    def dealer_turn(self):
        """
        Monitors the dealer's hand state via the API and animates new cards.

        This method polls the API to see the dealer's final hand. If the
        local table is missing cards, it adds them one by one to create
        a natural dealing sequence.
        """
        try:
            response = requests.get('http://blackjack-api:8000/blackjack/state')
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"State API Error: {e}")
            return

        # Check if the dealer hand on the API is larger than what we see on screen.
        if len(self.dealer_cards) < len(data["dealer_hand"]):
            new_index = len(self.dealer_cards)
            new_card = Card(self, BLACKJACK_CARD_START_LOCATION)

            self.dealer_cards.append(new_card)
            self.blackjack_cards.append(new_card)

            # Setup card identity and target coordinates.
            new_card.set_front(data["dealer_hand"][new_index])
            new_card.target_location = pygame.Vector2(
                BLACKJACK_DEALER_LOCATION[0] + BLACKJACK_CARD_HELD_OFFSET * (len(self.dealer_cards) - 1),
                BLACKJACK_DEALER_LOCATION[1])

            new_card.moving = True
            new_card.move_then_flip = True

            # Update score UI.
            self.dealer_score.set_text(str(data["dealer_total"]))

            # Pause logic until this new card finishes moving/flipping.
            self.game_state = BlackjackGameState.WAITING_DEALER_CARD
        else:
            # Table hand matches API hand; the round is visually complete.
            # TODO: Transition to a GAME_OVER state to display "You Win/Lose" before resetting.
            self.end_game_early()

    def end_game_early(self):
        """
        Handles immediate game conclusions (e.g., Natural Blackjacks or initial Busts).

        Resets UI buttons to allow the player to start a new round.
        """
        self.hit_button.disable()
        self.stand_button.disable()

        # Return control to the player for the next round setup
        self.deal_button.enable()
        self.reset_button.enable()
        self.chip_container.enable()

        self.game_state = BlackjackGameState.PRE_DEAL