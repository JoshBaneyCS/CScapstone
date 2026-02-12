"""Texas Hold'em Poker API using FastAPI."""

import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, PrivateAttr

app = FastAPI(title="Texas Hold'em API")

# ruff: noqa: PLR2004, PLW0603, SLF001

# python -m uvicorn apps.main:app --reload


# ----- Models -----
class StartRequest(BaseModel):
    """Request to start a new game."""

    players: int = 2
    bet: int = 1


class SingleStartRequest(BaseModel):
    """Request to start a single-player game (player vs CPU)."""

    player_bankroll: int = 100
    cpu_bankroll: int = 100
    cpu_players: int = 4
    bet: int = 10


class ActionRequest(BaseModel):
    """Request to take an action in a single-player round."""

    action: str  # stay, raise, fold
    amount: int | None = 0


class BetRequest(BaseModel):
    """Request to place the initial bet for a round."""

    amount: int


class GameState(BaseModel):
    """Current game state."""

    players_hands: dict[str, list[str]]
    community_cards: list[str]
    status: str  # preflop, flop, turn, river, showdown, finished
    bet: int
    winning_number: tuple[int, list[int]] | None = None
    winners: list[str] | None = None

    # single-player fields
    mode: str | None = None  # None or "single"
    cpu_players: list[str] | None = None
    pot: int | None = None
    current_bet: int | None = None
    round_bets: dict[str, int] | None = None
    player_stacks: dict[str, int] | None = None
    folded: list[str] | None = None
    last_action: dict[str, str] | None = None
    to_act: str | None = None  # "player" or "cpu"
    last_small_blind: str | None = None

    # private deck (not serialized)
    _deck: list[str] = PrivateAttr(default_factory=list[str])  # deck is kept server-side


# ----- In-memory game state -----
TEXAS_GAME: GameState | None = None  # global singleton game state

# ----- Card helpers -----
SUITS = ["S", "H", "D", "C"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

RANK_VALUE = {r: i + 2 for i, r in enumerate(RANKS)}  # '2'->2 ... 'A'->14


def new_deck() -> list[str]:
    """Generate and return a new shuffled deck of cards."""
    deck = [f"{r}{s}" for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def draw(deck: list[str]) -> str:
    """Draw a card from the deck."""
    if not deck:
        raise HTTPException(status_code=500, detail="Deck is empty.")
    return deck.pop()


def parse_card(card: str) -> tuple[int, str]:
    """Parse a card string into (rank_value, suit)."""
    return RANK_VALUE[card[:-1]], card[-1]  # rank, suit


# ----- Poker hand evaluator -----
def _get_straight_high(ranks_set: set[int]) -> int | None:
    """Return highest rank of straight in ranks_set, or None if no straight."""
    # include ace as 1 for wheel
    ranks = set(ranks_set)
    if 14 in ranks:
        ranks.add(1)
    sorted_r = sorted(ranks)  # ascending sort for straight detection
    consec = 1  # consecutive count
    last = None
    best_high = None
    for r in sorted_r:  # for each rank in ascending order
        if last is None or r != last + 1:  # if not consecutive
            consec = 1  # reset count
        else:  # consecutive
            consec += 1  # increment count of consecutive ranks
        if consec >= 5:  # found a straight
            best_high = r  # update best high rank
        last = r  # update last rank
    return best_high


def evaluate_best_hand(cards: list[str]) -> tuple[int, list[int]]:
    """Return a comparable tuple (rank_value, tie_breakers).

    rank_value: 10 = royal flush, 9 = straight flush, 8 = four, 7 = full house, 6 = flush,
    5 = straight, 4 = three, 3 = two pair, 2 = one pair, 1 = high card
    tie_breakers: list of ranks descending used for breaking ties
    """
    ranks: list[int] = []
    suits_map: dict[str, list[int]] = {s: [] for s in SUITS}  # suit -> list of ranks
    for c in cards:  # for each card in hand
        r, s = parse_card(c)  # rank, suit
        ranks.append(r)
        suits_map[s].append(r)

    counts: dict[int, int] = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1

    # sort unique ranks desc
    unique_desc = sorted(set(ranks), reverse=True)

    # Check for flush
    flush_suit = None
    flush_ranks: list[int] = []
    for s, rs in suits_map.items():
        if len(rs) >= 5:
            flush_suit = s
            flush_ranks = sorted(rs, reverse=True)
            break

    # Check for straight flush
    if flush_suit is not None:
        sf_high = _get_straight_high(set(flush_ranks))
        if sf_high:
            # royal flush (A-high straight flush)
            if sf_high == 14:
                return 10, [14]
            return 9, [sf_high]

    # Four of a kind
    quads = [r for r, c in counts.items() if c == 4]
    if quads:
        q = max(quads)
        kickers = [r for r in unique_desc if r != q]
        return 8, [q, kickers[0]]

    # Full house (three + pair)
    trips = sorted([r for r, c in counts.items() if c >= 3], reverse=True)
    pairs = sorted([r for r, c in counts.items() if c >= 2 and r not in trips], reverse=True)
    if trips and (pairs or len(trips) >= 2):
        three = trips[0]
        pair = pairs[0] if pairs else trips[1]
        return 7, [three, pair]

    # Flush
    if flush_suit is not None:
        return 6, flush_ranks[:5]

    # Straight
    straight_high = _get_straight_high(set(ranks))
    if straight_high:
        return 5, [straight_high]

    # Three of a kind
    if trips:
        three = trips[0]
        kickers = [r for r in unique_desc if r != three][:2]  # top 2 kickers
        return 4, [three, *kickers]

    # Two pair
    pair_ranks = sorted([r for r, c in counts.items() if c == 2], reverse=True)  # all pairs
    if len(pair_ranks) >= 2:
        top1, top2 = pair_ranks[0], pair_ranks[1]
        kicker = next(r for r in unique_desc if r not in (top1, top2))  # top kicker
        return 3, [top1, top2, kicker]

    # One pair
    if len(pair_ranks) == 1:
        pair = pair_ranks[0]
        kickers = [r for r in unique_desc if r != pair][:3]  # top 3 kickers
        return 2, [pair, *kickers]

    # High card
    return 1, unique_desc[:5]


def compare_hands(cards_a: list[str], cards_b: list[str]) -> int:
    """Compare best hands for two players. Return 1 if a>b, -1 if a<b, 0 tie."""
    a_score = evaluate_best_hand(cards_a)
    b_score = evaluate_best_hand(cards_b)
    if a_score > b_score:
        return 1
    if a_score < b_score:
        return -1
    return 0


def _preflop_strength(hand: list[str]) -> int:
    """Rough preflop strength score for CPU logic."""
    r1, s1 = parse_card(hand[0])
    r2, s2 = parse_card(hand[1])
    score = 0
    if r1 == r2:
        score += 4
    high_cards = sum(1 for r in (r1, r2) if r >= 11)
    score += high_cards
    if max(r1, r2) >= 13:
        score += 1
    if s1 == s2:
        score += 1
    if abs(r1 - r2) == 1:
        score += 1
    return score


# ----- Game logic -----
def state() -> GameState:
    """Return current game state."""
    if TEXAS_GAME is None:
        raise HTTPException(
            status_code=400,
            detail="No active round. Call /texas/single/start first.",
        )
    return TEXAS_GAME


def _ensure_single() -> GameState:
    """Ensure a single-player game is active."""
    s = state()
    if s.mode != "single":
        raise HTTPException(status_code=400, detail="No active single-player round.")
    return s


def _active_players() -> list[str]:
    """Return active (not folded) players in the current hand."""
    if TEXAS_GAME is None:
        return []
    folded = set(TEXAS_GAME.folded or [])
    return [p for p in TEXAS_GAME.players_hands if p not in folded]


def _post_bet(player: str, amount: int) -> None:
    """Post a bet and update stacks/pot/current bet."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    if TEXAS_GAME.player_stacks is None or TEXAS_GAME.round_bets is None:
        raise HTTPException(status_code=500, detail="Single-player state not initialized.")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Bet amount must be > 0")
    if TEXAS_GAME.player_stacks[player] < amount:
        raise HTTPException(status_code=400, detail="Insufficient stack.")
    TEXAS_GAME.player_stacks[player] -= amount
    TEXAS_GAME.round_bets[player] += amount
    TEXAS_GAME.pot = (TEXAS_GAME.pot or 0) + amount
    TEXAS_GAME.current_bet = max(TEXAS_GAME.current_bet or 0, TEXAS_GAME.round_bets[player])


def _call_or_check(player: str) -> int:
    """Call up to current bet or check if nothing to call."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    if TEXAS_GAME.player_stacks is None or TEXAS_GAME.round_bets is None:
        raise HTTPException(status_code=500, detail="Single-player state not initialized.")
    to_call = (TEXAS_GAME.current_bet or 0) - TEXAS_GAME.round_bets[player]
    if to_call <= 0:
        return 0
    call_amt = min(to_call, TEXAS_GAME.player_stacks[player])
    TEXAS_GAME.player_stacks[player] -= call_amt
    TEXAS_GAME.round_bets[player] += call_amt
    TEXAS_GAME.pot = (TEXAS_GAME.pot or 0) + call_amt
    return call_amt


def _round_settled() -> bool:
    """Check if all active players have matched the current bet."""
    if TEXAS_GAME is None:
        return False
    if TEXAS_GAME.round_bets is None or TEXAS_GAME.current_bet is None:
        return False
    active_players = _active_players()
    if not active_players:
        return True
    for player in active_players:
        player_stack = (TEXAS_GAME.player_stacks or {}).get(player, 0)
        if player_stack == 0:
            continue
        if TEXAS_GAME.round_bets.get(player, 0) != (TEXAS_GAME.current_bet or 0):
            return False
    return True


def _advance_stage() -> None:
    """Advance the hand stage and reset round betting state."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    if TEXAS_GAME.status == "preflop":
        _deal_community(3)
        TEXAS_GAME.status = "flop"
    elif TEXAS_GAME.status == "flop":
        _deal_community(1)
        TEXAS_GAME.status = "turn"
    elif TEXAS_GAME.status == "turn":
        _deal_community(1)
        TEXAS_GAME.status = "river"
    elif TEXAS_GAME.status == "river":
        TEXAS_GAME.status = "showdown"
    if TEXAS_GAME.round_bets is not None:
        for player in TEXAS_GAME.round_bets:
            TEXAS_GAME.round_bets[player] = 0
    TEXAS_GAME.current_bet = 0
    TEXAS_GAME.to_act = "player"


def _settle_showdown() -> None:
    """Compute winners, split pot, and finalize the hand."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    community = TEXAS_GAME.community_cards
    scores: dict[str, tuple[int, list[int]]] = {}
    for player, hand in TEXAS_GAME.players_hands.items():
        if TEXAS_GAME.folded and player in TEXAS_GAME.folded:
            continue
        scores[player] = evaluate_best_hand(hand + community)  # score for each player
    best_players: list[str] = []
    best_score: tuple[int, list[int]] | None = None
    for p, sc in scores.items():
        if best_score is None or sc > best_score:  # found new best score
            best_score = sc
            best_players = [p]  # new winner list
        elif sc == best_score:  # tie for best score
            best_players.append(p)  # add to winners
    TEXAS_GAME.winners = best_players
    TEXAS_GAME.winning_number = best_score
    if TEXAS_GAME.player_stacks is not None:
        pot = TEXAS_GAME.pot or 0
        if best_players:
            split = pot // len(best_players)  # integer division for split pot
            remainder = pot % len(best_players)  # remainder to first winners
            for i, p in enumerate(best_players):
                TEXAS_GAME.player_stacks[p] += split + (1 if i < remainder else 0)  # split pot
    TEXAS_GAME.status = "finished"


def _cpu_decide_action(cpu_name: str) -> tuple[str, int]:
    """Decide CPU decision based on hand strength and bet to call."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    cpu_hand = TEXAS_GAME.players_hands.get(cpu_name, [])
    to_call = (TEXAS_GAME.current_bet or 0) - (TEXAS_GAME.round_bets or {}).get(cpu_name, 0)
    cpu_stack = (TEXAS_GAME.player_stacks or {}).get(cpu_name, 0)
    if TEXAS_GAME.status == "preflop":
        strength = _preflop_strength(cpu_hand)
    else:
        strength = evaluate_best_hand(cpu_hand + TEXAS_GAME.community_cards)[0]
    action = "stay"
    amount = 0

    if to_call == 0 and strength >= 5 and cpu_stack > 0:
        action = "raise"
        amount = min(5, cpu_stack)  # small raise
    elif to_call > 0 and strength >= 6 and cpu_stack > to_call + 5:
        action = "raise"
        amount = 5  # small raise
    elif to_call > 0 and ((strength >= 4 and to_call <= 10) or to_call <= 2):
        action = "stay"
    elif to_call > 0:
        action = "fold"

    return action, amount


def _finish_on_fold(folding_player: str) -> None:
    """End the hand immediately when a player folds."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    if TEXAS_GAME.folded is None:
        TEXAS_GAME.folded = []
    if folding_player not in TEXAS_GAME.folded:
        TEXAS_GAME.folded.append(folding_player)
    remaining = _active_players()
    if folding_player == "Player" or len(remaining) <= 1:
        TEXAS_GAME.winners = remaining
        if TEXAS_GAME.player_stacks is not None and remaining:
            pot = TEXAS_GAME.pot or 0
            split = pot // len(remaining)
            remainder = pot % len(remaining)
            for i, p in enumerate(remaining):
                TEXAS_GAME.player_stacks[p] += split + (1 if i < remainder else 0)
        TEXAS_GAME.status = "finished"


def _cpu_take_turns() -> None:
    """Execute CPU actions in order and return control to player."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    cpu_players = TEXAS_GAME.cpu_players or []
    for cpu_name in cpu_players:
        if TEXAS_GAME.folded and cpu_name in TEXAS_GAME.folded:
            continue
        if TEXAS_GAME.status == "finished":
            return
        action, amount = _cpu_decide_action(cpu_name)
        if TEXAS_GAME.last_action is None:
            TEXAS_GAME.last_action = {}
        TEXAS_GAME.last_action[cpu_name] = action
        if action == "fold":
            _finish_on_fold(cpu_name)
            if TEXAS_GAME.status == "finished":
                return
            continue
        if action == "stay":
            _call_or_check(cpu_name)
        elif action == "raise":
            _call_or_check(cpu_name)
            if amount > 0:
                _post_bet(cpu_name, amount)
    TEXAS_GAME.to_act = "player"


def _maybe_progress_round() -> None:
    """Advance stages or settle showdown when bets are matched."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round.")
    if TEXAS_GAME.status in ("finished", "showdown"):
        if TEXAS_GAME.status == "showdown":
            _settle_showdown()
        return
    if len(_active_players()) <= 1:
        TEXAS_GAME.winners = _active_players()
        if TEXAS_GAME.player_stacks is not None and TEXAS_GAME.winners:
            TEXAS_GAME.player_stacks[TEXAS_GAME.winners[0]] += TEXAS_GAME.pot or 0
        TEXAS_GAME.status = "finished"
        return
    if _round_settled():
        _advance_stage()
        if TEXAS_GAME.status == "showdown":
            _settle_showdown()


# ----- Endpoints -----
@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Texas Hold'em API is running"}


@app.post("/texas/single/start")
def single_start(req: SingleStartRequest) -> GameState:
    """Start a new single-player Texas Hold'em game."""
    global TEXAS_GAME
    if req.bet <= 0:
        raise HTTPException(status_code=400, detail="Blind must be > 0")
    if req.player_bankroll <= 0 or req.cpu_bankroll <= 0:
        raise HTTPException(status_code=400, detail="Bankrolls must be > 0")
    if req.cpu_players < 1 or req.cpu_players > 7:
        raise HTTPException(status_code=400, detail="CPU players must be between 1 and 7")

    deck = new_deck()
    cpu_players = [f"CPU{i + 1}" for i in range(req.cpu_players)]
    turn_order = ["Player", *cpu_players]
    players_hands: dict[str, list[str]] = {"Player": [draw(deck), draw(deck)]}
    for cpu_name in cpu_players:
        players_hands[cpu_name] = [draw(deck), draw(deck)]

    round_bets = {"Player": 0}
    player_stacks = {"Player": req.player_bankroll}
    for cpu_name in cpu_players:
        round_bets[cpu_name] = 0
        player_stacks[cpu_name] = req.cpu_bankroll

    small_blind = max(1, req.bet // 2)
    big_blind = req.bet
    small_blind_player = turn_order[0]
    big_blind_player = turn_order[1 % len(turn_order)]

    if player_stacks[small_blind_player] < small_blind:
        raise HTTPException(status_code=400, detail="Small blind stack too low")
    if player_stacks[big_blind_player] < big_blind:
        raise HTTPException(status_code=400, detail="Big blind stack too low")

    pot = 0
    player_stacks[small_blind_player] -= small_blind
    round_bets[small_blind_player] += small_blind
    pot += small_blind
    player_stacks[big_blind_player] -= big_blind
    round_bets[big_blind_player] += big_blind
    pot += big_blind

    TEXAS_GAME = GameState(
        players_hands=players_hands,
        community_cards=[],
        bet=req.bet,
        status="preflop",
        mode="single",
        cpu_players=cpu_players,
        pot=pot,
        current_bet=big_blind,
        round_bets=round_bets,
        player_stacks=player_stacks,
        folded=[],
        last_action={},
        to_act="player",
        last_small_blind=small_blind_player,
    )
    TEXAS_GAME._deck = deck

    # Check actions for CPUs 2 through 4
    for i in range(1, min(4, len(cpu_players))):
        cpu_name = cpu_players[i]
        if TEXAS_GAME.status == "finished":
            break
        action, amount = _cpu_decide_action(cpu_name)
        if TEXAS_GAME.last_action is None:
            TEXAS_GAME.last_action = {}
        TEXAS_GAME.last_action[cpu_name] = action
        if action == "fold":
            _finish_on_fold(cpu_name)
            continue
        if action == "stay":
            _call_or_check(cpu_name)
        elif action == "raise":
            _call_or_check(cpu_name)
            if amount > 0:
                _post_bet(cpu_name, amount)
    TEXAS_GAME.to_act = "player"  # ensure player gets first action after blinds

    return state()


@app.post("/texas/single/action")
def single_action(req: ActionRequest) -> GameState:
    """Player action: stay (check/call), raise, or fold."""
    s = _ensure_single()
    if s.to_act != "player":
        raise HTTPException(status_code=400, detail="Not player's turn.")
    if s.status not in ("preflop", "flop", "turn", "river"):
        raise HTTPException(status_code=400, detail=f"Invalid state: {s.status}")

    action = req.action.lower()
    if action not in ("stay", "raise", "fold"):
        raise HTTPException(status_code=400, detail="Invalid action.")

    if s.last_action is None:
        s.last_action = {}
    s.last_action["Player"] = action

    if action == "fold":
        _finish_on_fold("Player")
        return state()

    if action == "stay":
        _call_or_check("Player")
    elif action == "raise":
        if not req.amount or req.amount <= 0:
            raise HTTPException(status_code=400, detail="Raise amount must be > 0")
        _call_or_check("Player")
        _post_bet("Player", req.amount)

    s.to_act = "cpu"
    _cpu_take_turns()
    if s.status != "finished" and s.to_act == "player" and _round_settled():
        _maybe_progress_round()
    return state()


def _deal_community(n: int) -> None:
    """Deal n community cards."""
    if TEXAS_GAME is None:
        raise HTTPException(
            status_code=400,
            detail="No active round. Call /texas/single/start first.",
        )
    for _ in range(n):
        TEXAS_GAME.community_cards.append(draw(TEXAS_GAME._deck))


@app.post("/texas/flop")
def flop() -> GameState:
    """Deal the flop (3 community cards)."""
    if TEXAS_GAME is None:
        raise HTTPException(
            status_code=400,
            detail="No active round. Call /texas/single/start first.",
        )
    s = state()
    if s.status != "preflop":
        raise HTTPException(status_code=400, detail=f"Invalid state for flop: {s.status}")
    if not _round_settled():
        raise HTTPException(status_code=400, detail="Not all players have settled their bets.")
    _deal_community(3)
    TEXAS_GAME.status = "flop"
    return state()


@app.post("/texas/turn")
def turn() -> GameState:
    """Deal the turn (1 community card)."""
    if TEXAS_GAME is None:
        raise HTTPException(
            status_code=400,
            detail="No active round. Call /texas/single/start first.",
        )
    s = state()
    if s.status not in ("flop",):
        raise HTTPException(status_code=400, detail=f"Invalid state for turn: {s.status}")
    if not _round_settled():
        raise HTTPException(status_code=400, detail="Not all players have settled their bets.")
    _deal_community(1)
    TEXAS_GAME.status = "turn"
    return state()


@app.post("/texas/river")
def river() -> GameState:
    """Deal the river (1 community card)."""
    if TEXAS_GAME is None:
        raise HTTPException(
            status_code=400,
            detail="No active round. Call /texas/single/start first.",
        )
    s = state()
    if s.status not in ("turn",):
        raise HTTPException(status_code=400, detail=f"Invalid state for river: {s.status}")
    if not _round_settled():
        raise HTTPException(status_code=400, detail="Not all players have settled their bets.")
    _deal_community(1)
    TEXAS_GAME.status = "river"
    return state()


@app.post("/texas/showdown")
def showdown() -> GameState:
    """Evaluate hands and determine winner(s)."""
    if TEXAS_GAME is None:
        raise HTTPException(
            status_code=400,
            detail="No active round. Call /texas/single/start first.",
        )
    s = state()
    if s.status not in ("river",):
        raise HTTPException(status_code=400, detail=f"Invalid state for showdown: {s.status}")
    if not _round_settled():
        raise HTTPException(status_code=400, detail="Not all players have settled their bets.")

    # Evaluate all players
    community = TEXAS_GAME.community_cards
    scores: dict[str, tuple[int, list[int]]] = {}
    for player, hand in TEXAS_GAME.players_hands.items():
        if TEXAS_GAME.folded and player in TEXAS_GAME.folded:
            continue
        combined = hand + community  # player's full hand
        scores[player] = evaluate_best_hand(combined)

    # find best
    best_players: list[str] = []
    best_score: tuple[int, list[int]] | None = None
    for p, sc in scores.items():  # player, score
        if best_score is None or sc > best_score:  # found new best score
            best_score = sc
            best_players = [p]  # new winner list
        elif sc == best_score:
            best_players.append(p)  # tie for best score

    TEXAS_GAME.winners = best_players
    TEXAS_GAME.status = "finished"
    TEXAS_GAME.winning_number = best_score
    if TEXAS_GAME.player_stacks is not None:
        pot = TEXAS_GAME.pot or 0
        if best_players:
            split = pot // len(best_players)
            remainder = pot % len(best_players)
            for i, p in enumerate(best_players):
                TEXAS_GAME.player_stacks[p] += split + (1 if i < remainder else 0)
    return state()


@app.get("/texas/state")
def get_state() -> GameState:
    """Get current game state."""
    return state()
