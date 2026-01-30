import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, PrivateAttr

app = FastAPI(title="Texas Hold'em API")

# ruff: noqa: PLR2004


# ----- Models -----
class StartRequest(BaseModel):
    """Request to start a new game."""

    players: int = 2
    bet: int = 1


class GameState(BaseModel):
    """Current game state."""

    players_hands: dict[str, list[str]]
    community_cards: list[str]
    status: str  # preflop, flop, turn, river, showdown, finished
    bet: int
    winning_number: tuple[int, list[int]] | None = None
    winners: list[str] | None = None

    # private deck (not serialized)
    _deck: list[str] = PrivateAttr(default_factory=list[str])


# ----- In-memory game state -----
TEXAS_GAME: GameState | None = None

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
    return RANK_VALUE[card[:-1]], card[-1]


# ----- Poker hand evaluator -----
def _get_straight_high(ranks_set: set[int]) -> int | None:
    """Return highest rank of straight in ranks_set, or None if no straight."""
    # include ace as 1 for wheel
    ranks = set(ranks_set)
    if 14 in ranks:
        ranks.add(1)
    sorted_r = sorted(ranks)
    consec = 1
    last = None
    best_high = None
    for r in sorted_r:
        if last is None or r != last + 1:
            consec = 1
        else:
            consec += 1
        if consec >= 5:
            best_high = r
        last = r
    return best_high


def evaluate_best_hand(cards: list[str]) -> tuple[int, list[int]]:
    """Return a comparable tuple (rank_value, tie_breakers).

    rank_value: 10 = royal flush, 9 = straight flush, 8 = four, 7 = full house, 6 = flush,
    5 = straight, 4 = three, 3 = two pair, 2 = one pair, 1 = high card
    tie_breakers: list of ranks descending used for breaking ties
    """
    ranks: list[int] = []
    suits_map: dict[str, list[int]] = {s: [] for s in SUITS}
    for c in cards:
        r, s = parse_card(c)
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
        kickers = [r for r in unique_desc if r != three][:2]
        return 4, [three, *kickers]

    # Two pair
    pair_ranks = sorted([r for r, c in counts.items() if c == 2], reverse=True)
    if len(pair_ranks) >= 2:
        top1, top2 = pair_ranks[0], pair_ranks[1]
        kicker = next(r for r in unique_desc if r not in (top1, top2))
        return 3, [top1, top2, kicker]

    # One pair
    if len(pair_ranks) == 1:
        pair = pair_ranks[0]
        kickers = [r for r in unique_desc if r != pair][:3]
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


# ----- Game logic -----
def state() -> GameState:
    """Return current game state."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round. Call /texas/start first.")
    return TEXAS_GAME


# ----- Endpoints -----
@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Texas Hold'em API is running"}


@app.post("/texas/start")
def start(req: StartRequest) -> GameState:
    """Start a new Texas Hold'em game."""
    global TEXAS_GAME
    if req.bet <= 0:
        raise HTTPException(status_code=400, detail="Bet must be > 0")
    if req.players < 2 or req.players > 8:
        raise HTTPException(status_code=400, detail="Players must be between 2 and 8")

    deck = new_deck()
    players_hands: dict[str, list[str]] = {}
    for i in range(req.players):
        players_hands[f"Player {i + 1}"] = [draw(deck), draw(deck)]

    TEXAS_GAME = GameState(
        players_hands=players_hands,
        community_cards=[],
        bet=req.bet,
        status="preflop",
    )
    TEXAS_GAME._deck = deck
    return state()


def _deal_community(n: int) -> None:
    """Deal n community cards."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round. Call /texas/start first.")
    for _ in range(n):
        TEXAS_GAME.community_cards.append(draw(TEXAS_GAME._deck))


@app.post("/texas/flop")
def flop() -> GameState:
    """Deal the flop (3 community cards)."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round. Call /texas/start first.")
    s = state()
    if s.status != "preflop":
        raise HTTPException(status_code=400, detail=f"Invalid state for flop: {s.status}")
    _deal_community(3)
    TEXAS_GAME.status = "flop"
    return state()


@app.post("/texas/turn")
def turn() -> GameState:
    """Deal the turn (1 community card)."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round. Call /texas/start first.")
    s = state()
    if s.status not in ("flop",):
        raise HTTPException(status_code=400, detail=f"Invalid state for turn: {s.status}")
    _deal_community(1)
    TEXAS_GAME.status = "turn"
    return state()


@app.post("/texas/river")
def river() -> GameState:
    """Deal the river (1 community card)."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round. Call /texas/start first.")
    s = state()
    if s.status not in ("turn",):
        raise HTTPException(status_code=400, detail=f"Invalid state for river: {s.status}")
    _deal_community(1)
    TEXAS_GAME.status = "river"
    return state()


@app.post("/texas/showdown")
def showdown() -> GameState:
    """Evaluate hands and determine winner(s)."""
    if TEXAS_GAME is None:
        raise HTTPException(status_code=400, detail="No active round. Call /texas/start first.")
    s = state()
    if s.status not in ("river",):
        raise HTTPException(status_code=400, detail=f"Invalid state for showdown: {s.status}")

    # Evaluate all players
    community = TEXAS_GAME.community_cards
    scores: dict[str, tuple[int, list[int]]] = {}
    for player, hand in TEXAS_GAME.players_hands.items():
        combined = hand + community
        scores[player] = evaluate_best_hand(combined)

    # find best
    best_players: list[str] = []
    best_score: tuple[int, list[int]] | None = None
    for p, sc in scores.items():  # player, score
        if best_score is None or sc > best_score:
            best_score = sc
            best_players = [p]
        elif sc == best_score:
            best_players.append(p)

    TEXAS_GAME.winners = best_players
    TEXAS_GAME.status = "finished"
    TEXAS_GAME.winning_number = best_score
    return state()


@app.post("/texas/test/{win_needed}")
def texas_test(win_needed: int) -> GameState:
    """Run a test game until a given winning hand."""
    while True:
        start(StartRequest(players=4, bet=10))
        flop()
        turn()
        river()
        showdown()
        wn = state().winning_number
        if wn and wn[0] == win_needed:
            return state()


@app.get("/texas/state")
def get_state() -> GameState:
    """Get current game state."""
    return state()


if __name__ == "__main__":
    for i in range(1, 11):
        print(texas_test(i))
