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

class BlackjackGameState(Enum):
    SETUP = 0
    PRE_DEAL = 1
    START_DEAL = 2
    DEALING = 3
    DEALT = 4
    PLAYER_TURN = 5
    GIVE_PLAYER_CARD = 6
    WAITING_PLAYER_CARD = 7
    RESOLVING_HIT = 8
    PLAYER_STANDS = 9
    DEALER_FLIPS = 10
    WAITING_DEALER_CARD = 11
    DEALER_TURN = 12
    GIVE_DEALER_CARD = 13
    GAME_OVER = 14

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

## Game Menu
TITLE_SIZE = (900, 120)
TITLE_Y_LOCATION = 200
GAME_BUTTON_SIZE = (150, 50)
POKER_BUTTON_Y_LOCATION = 490
BLACKJACK_BUTTON_Y_LOCATION = 580
CREDITS_BUTTON_Y_LOCATION = 670

## Blackjack
BLACKJACK_BUTTON_SIZE = (150, 50)
BLACKJACK_HIT_BUTTON_X_DELTA = 400
BLACKJACK_STAND_BUTTON_X_DELTA = -400
BLACKJACK_ACTION_BUTTON_Y = 540
BLACKJACK_BET_AMOUNT_SIZE = (200, 55)
BLACKJACK_BET_AMOUNT_LOCATION = (200 - BLACKJACK_BET_AMOUNT_SIZE[0] / 2, 600)
BLACKJACK_DEAL_BUTTON_LOCATION = (400 - BLACKJACK_BUTTON_SIZE[0] / 2, 600)
BLACKJACK_RESET_BUTTON_LOCATION = (560 - BLACKJACK_BUTTON_SIZE[0] / 2, 600)
BLACKJACK_CHIP_CONTAINER_SIZE = (620, 420)
BLACKJACK_CHIP_CONTAINER_LOCATION = (50, 1080 - BLACKJACK_CHIP_CONTAINER_SIZE[1] - 10)
BLACKJACK_CHIP_SIZE = (200, 200)
BLACKJACK_WHITE_CHIP_LOCATION = TOP_LEFT
BLACKJACK_RED_CHIP_LOCATION = (200, 0)
BLACKJACK_GREEN_CHIP_LOCATION = (400, 0)
BLACKJACK_BLUE_CHIP_LOCATION = (100, 200)
BLACKJACK_BLACK_CHIP_LOCATION = (300, 200)
BLACKJACK_SCORE_SIZE = (55, 55)
BLACKJACK_PLAYER_SCORE_LOCATION = (1400, 740)
BLACKJACK_DEALER_SCORE_LOCATION = (1400, 340)
BLACKJACK_CARD_START_LOCATION = (2000, -200)
BLACKJACK_PLAYER_LOCATION = (900, 650)
BLACKJACK_DEALER_LOCATION = (900, 270)
BLACKJACK_CARD_HELD_OFFSET = 50
BLACKJACK_BALANCE_LABEL_SIZE = (250, 55)
BLACKJACK_BALANCE_LABEL_LOCATION = (50, 50)
BLACKJACK_RESULT_LABEL_SIZE = (400, 60)
BLACKJACK_STARTING_BALANCE = 2500

## Poker
POKER_DECK_LOCATION = (1575, 130)
POKER_PLAYER_LOCATION = (840, 360)
POKER_AI_LOCATION = (840, 710)

## Base display that contains all the functionality shared by each screen, including the settings menu
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

## Lets the user choose between all available casino card games
class GameMenu(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
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
        self.credits_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(GAME_BUTTON_SIZE[0]), CREDITS_BUTTON_Y_LOCATION),
                GAME_BUTTON_SIZE),
            text='Credits',
            manager=self.ui_manager,
            container=self.scene_container)
        self.credits_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                (self.game.screen_width / 2 - self.game.GAME_RESOLUTION[0] / 2,
                 self.game.screen_height / 2 - self.game.GAME_RESOLUTION[1] / 2),
                self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            starting_height=100,
            visible=False,
            container=self.game.canvas,
            object_id='@credits_panel')

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.poker_button:
                        self.game.change_scene(SceneID.POKER)
                    case self.blackjack_button:
                        self.game.change_scene(SceneID.BLACKJACK)
                    case self.credits_button:
                        self.play_credits()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    self.credits_panel.disable()
                    self.credits_panel.hide()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.credits_panel.disable()
                    self.credits_panel.hide()


            self.ui_manager.process_events(event)

    def update_scene(self):
        return

    def draw_scene(self):
        Scene.draw_scene(self)

    def play_credits(self):
        scrolling_text = "<br>".join(credits.CREDITS_STRINGS)
        self.credits_panel.enable()
        self.credits_panel.show()
        text_box = pygame_gui.elements.UITextBox(
            html_text=scrolling_text,
            relative_rect=pygame.Rect(
                TOP_LEFT,
                self.game.GAME_RESOLUTION),
            manager=self.ui_manager,
            container=self.credits_panel
        )
        text_box.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)

class BlackjackScene(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        self.game_state = BlackjackGameState.SETUP
        self.bet_amount = WHITE_CHIP_WORTH
        self.api_response = ""
        self.player_cards = []
        self.blackjack_cards = []
        self.leave_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(LEAVE_BUTTON_LOCATION, LEAVE_BUTTON_SIZE),
            text='Leave',
            manager=self.ui_manager,
            container=self.scene_container)
        self.deal_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_DEAL_BUTTON_LOCATION,
                BLACKJACK_BUTTON_SIZE),
            text='Deal',
            manager=self.ui_manager,
            container=self.scene_container)
        self.reset_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                BLACKJACK_RESET_BUTTON_LOCATION,
                BLACKJACK_BUTTON_SIZE),
            text='Reset',
            manager=self.ui_manager,
            container=self.scene_container)
        self.bet_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BLACKJACK_BET_AMOUNT_LOCATION,
                BLACKJACK_BET_AMOUNT_SIZE),
            text="$" + str(self.bet_amount),
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.chip_container = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                BLACKJACK_CHIP_CONTAINER_LOCATION,
                BLACKJACK_CHIP_CONTAINER_SIZE),
            manager=self.ui_manager,
            container=self.scene_container,
            starting_height=90,
            object_id=ObjectID(class_id='@popup_background'))
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
        self.hit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.center_x(BLACKJACK_HIT_BUTTON_X_DELTA), BLACKJACK_ACTION_BUTTON_Y),
                BLACKJACK_BUTTON_SIZE),
            text='Hit',
            manager=self.ui_manager,
            visible=False,
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
                BLACKJACK_PLAYER_SCORE_LOCATION,
                BLACKJACK_SCORE_SIZE),
            text='0',
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

        self.balance = BLACKJACK_STARTING_BALANCE
        self.stand_data = None
        self.balance_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                BLACKJACK_BALANCE_LABEL_LOCATION,
                BLACKJACK_BALANCE_LABEL_SIZE),
            text=f"${self.balance:.2f}",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.result_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (self.center_x(BLACKJACK_RESULT_LABEL_SIZE[0]), 500),
                BLACKJACK_RESULT_LABEL_SIZE),
            text="",
            manager=self.ui_manager,
            container=self.scene_container,
            object_id="#bet_amount")
        self.result_label.hide()

        self.reset_board()

    def open_scene(self):
        super().open_scene()
        self.reset_board()
        self.game_state = BlackjackGameState.SETUP
        self.result_label.hide()
        self.bet_amount = WHITE_CHIP_WORTH
        self.bet_label.set_text("$" + str(self.bet_amount))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.leave_button:
                        self.game.change_scene(SceneID.GAME_MENU)
                        return True
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
                    case self.deal_button:
                        self.game_state = BlackjackGameState.START_DEAL
                    case self.hit_button:
                        self.game_state = BlackjackGameState.GIVE_PLAYER_CARD
                    case self.stand_button:
                        self.game_state = BlackjackGameState.PLAYER_STANDS
            self.ui_manager.process_events(event)

    def draw_scene(self):
        ## Called once per frame, but there should only be 4-10 cards to check
        # and only 1-2 will be flipping at a time
        for card in self.blackjack_cards:
            if card.moving:
                card.move_card()
            if card.flipping:
                card.flip_card()
        Scene.draw_scene(self)

    def update_scene(self):
        match self.game_state:
            case BlackjackGameState.SETUP:
                self.hit_button.disable()
                self.stand_button.disable()
                self.player_score.hide()
                self.dealer_score.hide()
                self.game_state = BlackjackGameState.PRE_DEAL
            case BlackjackGameState.PRE_DEAL:
                return
            case BlackjackGameState.START_DEAL:
                self.deal_blackjack()
            case BlackjackGameState.DEALING:
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

        for card in self.blackjack_cards:
            card.image.kill()

        self.player_cards = [
            Card(self, BLACKJACK_CARD_START_LOCATION),
            Card(self, BLACKJACK_CARD_START_LOCATION) ]
        self.dealer_cards = [
            Card(self, BLACKJACK_CARD_START_LOCATION),
            Card(self, BLACKJACK_CARD_START_LOCATION) ]

        self.blackjack_cards = self.player_cards.copy()
        self.blackjack_cards.extend(self.dealer_cards)

        self.player_score.set_text("0")
        self.dealer_score.set_text("0")

    def deal_blackjack(self):
        self.reset_board()
        self.deal_button.disable()
        self.reset_button.disable()
        self.chip_container.disable()
        self.result_label.hide()
        self.balance -= self.bet_amount
        self.balance_label.set_text(f"${self.balance:.2f}")
        payload = {'bet': str(self.bet_amount)}
        try:
            response = requests.post('http://blackjack-api:8000/blackjack/start', data=json.dumps(payload))
            data = response.json()
        except Exception:
            self.balance += self.bet_amount
            self.balance_label.set_text(f"${self.balance:.2f}")
            self.finish_hand("error")
            return
        self.player_cards[0].set_front(data["player_hand"][0])
        self.player_cards[1].set_front(data["player_hand"][1])
        self.player_cards[0].target_location = pygame.Vector2(BLACKJACK_PLAYER_LOCATION)
        self.player_cards[1].target_location = pygame.Vector2(
            BLACKJACK_PLAYER_LOCATION[0] + 50, BLACKJACK_PLAYER_LOCATION[1])
        self.player_cards[0].moving = True
        self.player_cards[1].moving = True
        self.player_cards[0].move_then_flip = True
        self.player_cards[1].move_then_flip = True
        self.dealer_cards[0].set_front(data["dealer_hand"][0])
        self.dealer_cards[1].set_front(data["dealer_hand"][1])
        self.dealer_cards[0].target_location = pygame.Vector2(BLACKJACK_DEALER_LOCATION)
        self.dealer_cards[1].target_location = pygame.Vector2(
            BLACKJACK_DEALER_LOCATION[0] + 50, BLACKJACK_DEALER_LOCATION[1])
        self.dealer_cards[0].moving = True
        self.dealer_cards[1].moving = True
        self.dealer_cards[1].move_then_flip = True
        self.player_score.set_text(str(data["player_total"]))
        ## TODO: only count score from card showing, update later when dealers card flips
        self.dealer_score.set_text(str(data["dealer_total"]))

        self.check_for_blackjack()

    def check_for_blackjack(self):
        ## check for blackjack
        try:
            response = requests.get('http://blackjack-api:8000/blackjack/state')
            data = response.json()
        except Exception:
            self.finish_hand("error")
            return
        match data["status"]:
            case "dealer_win":
                self.finish_hand("dealer_win")
            case "player_win":
                self.finish_hand("player_win")
            case "push":
                self.finish_hand("push")
            case _:
                self.game_state = BlackjackGameState.DEALING

    def give_player_card(self):
        self.hit_button.disable()
        self.stand_button.disable()
        try:
            response = requests.post('http://blackjack-api:8000/blackjack/hit')
            data = response.json()
        except Exception:
            self.finish_hand("error")
            return
        new_card = Card(self, BLACKJACK_CARD_START_LOCATION)
        self.player_cards.append(new_card)
        self.blackjack_cards.append(self.player_cards[-1])
        self.player_cards[-1].set_front(data["player_hand"][-1])
        self.player_cards[-1].target_location = pygame.Vector2(
            BLACKJACK_PLAYER_LOCATION[0] + BLACKJACK_CARD_HELD_OFFSET * (len(self.player_cards) - 1),
            BLACKJACK_PLAYER_LOCATION[1])
        self.player_cards[-1].moving = True
        self.player_cards[-1].move_then_flip = True
        self.player_score.set_text(str(data["player_total"]))
        self.game_state = BlackjackGameState.RESOLVING_HIT

    def resolve_hit(self):
        try:
            response = requests.get('http://blackjack-api:8000/blackjack/state')
            data = response.json()
        except Exception:
            self.finish_hand("error")
            return
        match data["status"]:
            case "player_bust":
                self.finish_hand("player_bust")
            case "player_win":
                self.finish_hand("player_win")
            case "in_progress":
                self.hit_button.enable()
                self.stand_button.enable()
                self.game_state = BlackjackGameState.PLAYER_TURN

    def player_stands(self):
        self.hit_button.disable()
        self.stand_button.disable()
        try:
            response = requests.post('http://blackjack-api:8000/blackjack/stand')
            self.stand_data = response.json()
        except Exception:
            self.finish_hand("error")
            return
        self.dealer_cards[0].flipping = True
        self.game_state = BlackjackGameState.WAITING_DEALER_CARD

    def dealer_turn(self):
        data = self.stand_data
        if len(self.dealer_cards) < len(data["dealer_hand"]):
            new_index = len(self.dealer_cards)
            new_card = Card(self, BLACKJACK_CARD_START_LOCATION)
            self.dealer_cards.append(new_card)
            self.blackjack_cards.append(self.dealer_cards[-1])
            self.dealer_cards[-1].set_front(data["dealer_hand"][new_index])
            self.dealer_cards[-1].target_location = pygame.Vector2(
                BLACKJACK_DEALER_LOCATION[0] + BLACKJACK_CARD_HELD_OFFSET * (len(self.dealer_cards) - 1),
                BLACKJACK_DEALER_LOCATION[1])
            self.dealer_cards[-1].moving = True
            self.dealer_cards[-1].move_then_flip = True
            self.dealer_score.set_text(str(data["dealer_total"]))
            self.game_state = BlackjackGameState.WAITING_DEALER_CARD
        else:
            self.finish_hand(data["status"])

    def finish_hand(self, status):
        if status in ("player_win", "dealer_bust"):
            self.balance += self.bet_amount * 2
        elif status == "push":
            self.balance += self.bet_amount
        self.balance_label.set_text(f"${self.balance:.2f}")

        result_text = {
            "player_win": "You Win!",
            "dealer_bust": "You Win!",
            "dealer_win": "Dealer Wins",
            "player_bust": "Bust!",
            "push": "Push",
        }.get(status, "Game Over")
        self.result_label.set_text(result_text)
        self.result_label.show()

        self.hit_button.disable()
        self.stand_button.disable()
        self.deal_button.enable()
        self.reset_button.enable()
        self.white_chip.enable()
        self.red_chip.enable()
        self.green_chip.enable()
        self.blue_chip.enable()
        self.black_chip.enable()
        self.game_state = BlackjackGameState.PRE_DEAL

class PokerScene(Scene):
    def __init__(self, game):
        Scene.__init__(self, game)
        self.leave_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(LEAVE_BUTTON_LOCATION, LEAVE_BUTTON_SIZE),
            text='Leave',
            manager=self.ui_manager,
            container=self.scene_container)
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
                match event.ui_element:
                    case self.leave_button:
                        self.game.change_scene(SceneID.GAME_MENU)
                        return True
                """
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

