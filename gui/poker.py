# ----- Imports -----
from enum import Enum
import requests
import json
import pygame
import pygame_gui
from pygame_gui.core import ObjectID

from card import Card
from scene import (Scene, SceneID, WHITE_CHIP_WORTH, MENU_BUTTON_TEXT,
                   MENU_BUTTON_LOCATION, MENU_BUTTON_SIZE)


class PokerGameState(Enum):
    """Phases of a Texas Hold 'Em round corresponding to API actions."""
    SETUP = 0
    PRE_FLOP = 1
    FLOP = 2
    TURN = 3
    RIVER = 4
    SHOWDOWN = 5
    WAITING_ANIMATION = 6


# ----- Globals/Constants -----
POKER_API_BASE = 'http://poker-api:8001/texas'
POKER_PLAYER_POS = (900, 750)
POKER_COMMUNITY_POS = (600, 450)
POKER_CARD_GAP = 155  # Horizontal spacing for community cards


class PokerScene(Scene):
    """
    Texas Hold 'Em scene logic using port 8001 API.

    Coordinates multiple community card deals and sequential betting rounds.
    """

    def __init__(self, game):
        Scene.__init__(self, game)
        self.game_state = PokerGameState.SETUP
        self.next_poker_state = None
        self.player_hand = []
        self.community_cards = []
        self.all_cards = []

        # UI Elements
        self.menu_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(MENU_BUTTON_LOCATION, MENU_BUTTON_SIZE),
            text=MENU_BUTTON_TEXT, manager=self.ui_manager, container=self.scene_container)

        self.action_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((900, 900), (200, 60)),
            text="Start Game", manager=self.ui_manager, container=self.scene_container)

    def handle_events(self):
        """Processes poker actions: Start, Bet, Flop, Turn, River, and Showdown."""
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.menu_button:
                        self.game.change_scene(SceneID.GAME_MENU)
                    case self.action_button:
                        self.advance_game()
            self.ui_manager.process_events(event)

    def draw_scene(self):
        """Per-frame animation update for all cards on the poker table."""
        for card in self.all_cards:
            if card.moving: card.move_card()
            if card.flipping: card.flip_card()
        Scene.draw_scene(self)

    def update_scene(self):
        """Stalls logic transitions until card animations are visually complete."""
        if self.game_state == PokerGameState.WAITING_ANIMATION:
            if not any(c.moving or c.flipping for c in self.all_cards):
                self.game_state = self.next_poker_state
                self.update_ui_for_state()

    def advance_game(self):
        """Routes the 'Action' button to the correct API call based on game state."""
        match self.game_state:
            case PokerGameState.SETUP:
                self.api_call("single/start", PokerGameState.PRE_FLOP)
            case PokerGameState.PRE_FLOP:
                self.api_call("flop", PokerGameState.FLOP)
            case PokerGameState.FLOP:
                self.api_call("turn", PokerGameState.TURN)
            case PokerGameState.TURN:
                self.api_call("river", PokerGameState.RIVER)
            case PokerGameState.RIVER:
                self.api_call("showdown", PokerGameState.SHOWDOWN)
            case PokerGameState.SHOWDOWN:
                self.game_state = PokerGameState.SETUP

    def api_call(self, endpoint, next_state):
        """
        Generic POST wrapper for Poker API endpoints.

        Fetches state, instantiates new Card objects, and sets targets.
        """
        try:
            response = requests.post(f"{POKER_API_BASE}/{endpoint}")
            data = response.json()
            self.sync_table_with_api(data)
            self.next_poker_state = next_state
            self.game_state = PokerGameState.WAITING_ANIMATION
        except requests.exceptions.RequestException as e:
            print(f"Poker API Error: {e}")

    def sync_table_with_api(self, data):
        """
        Compares local Card hand to API hand and adds missing cards to the table.
        """
        # 1. Update Player Hole Cards (if empty)
        if not self.player_hand and "hole_cards" in data:
            for i, val in enumerate(data["hole_cards"]):
                card = Card(self, (2000, -200))
                card.set_front(val)
                card.target_location = pygame.Vector2(POKER_PLAYER_POS[0] + (i * 80), POKER_PLAYER_POS[1])
                card.moving = card.move_then_flip = True
                self.player_hand.append(card)
                self.all_cards.append(card)

        # 2. Update Community Cards
        api_community = data.get("community_cards", [])
        if len(self.community_cards) < len(api_community):
            for i in range(len(self.community_cards), len(api_community)):
                card = Card(self, (2000, -200))
                card.set_front(api_community[i])
                card.target_location = pygame.Vector2(POKER_COMMUNITY_POS[0] + (i * POKER_CARD_GAP),
                                                      POKER_COMMUNITY_POS[1])
                card.moving = card.move_then_flip = True
                self.community_cards.append(card)
                self.all_cards.append(card)

    def update_ui_for_state(self):
        """Updates the action button text to reflect the current betting round."""
        state_map = {
            PokerGameState.PRE_FLOP: "Deal Flop",
            PokerGameState.FLOP: "Deal Turn",
            PokerGameState.TURN: "Deal River",
            PokerGameState.RIVER: "Showdown",
            PokerGameState.SHOWDOWN: "New Game"
        }
        self.action_button.set_text(state_map.get(self.game_state, "Action"))

    def reset_table(self):
        """Cleans up UI elements and clears card trackers for a new hand."""
        for card in self.all_cards:
            card.image.kill()
        self.player_hand, self.community_cards, self.all_cards = [], [], []
