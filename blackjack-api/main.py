import asyncio
import time
from contextlib import asynccontextmanager
from typing import List, Dict, Any

import random
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


# ----- Session Management -----
SESSIONS: Dict[str, Dict[str, Any]] = {}  # user_id -> {"game": {...}, "last_active": timestamp}
SESSION_TTL_SECONDS = 3600  # 1 hour


def get_game(user_id: str) -> Dict[str, Any]:
    """Get the game state for a specific user."""
    session = SESSIONS.get(user_id)
    if session is None:
        raise HTTPException(status_code=400, detail="No active round. Call /blackjack/start first.")
    session["last_active"] = time.time()
    return session["game"]


def set_game(user_id: str, game: Dict[str, Any]) -> None:
    """Store game state for a specific user."""
    SESSIONS[user_id] = {"game": game, "last_active": time.time()}


def cleanup_sessions():
    """Remove expired sessions."""
    now = time.time()
    expired = [uid for uid, s in SESSIONS.items() if now - s["last_active"] > SESSION_TTL_SECONDS]
    for uid in expired:
        del SESSIONS[uid]


async def session_cleanup_loop():
    while True:
        cleanup_sessions()
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(session_cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title="Blackjack API", lifespan=lifespan)


# ----- Request/Response Models -----
class StartRequest(BaseModel):
    bet: int

class GameState(BaseModel):
    player_hand: List[str]
    dealer_hand: List[str]
    player_total: int
    dealer_total: int
    bet: int
    status: str  # in_progress, player_bust, dealer_bust, player_win, dealer_win, push


# ----- Card helpers -----
SUITS = ["S", "H", "D", "C"]
RANKS = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]

def new_deck() -> List[str]:
    deck = [f"{r}{s}" for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck

def draw(deck: List[str]) -> str:
    if not deck:
        raise HTTPException(status_code=500, detail="Deck is empty.")
    return deck.pop()

def hand_total(hand: List[str]) -> int:
    total = 0
    aces = 0
    for card in hand:
        rank = card[:-1]  # everything except suit
        if rank in ("J","Q","K"):
            total += 10
        elif rank == "A":
            total += 11
            aces += 1
        else:
            total += int(rank)

    # Convert Aces from 11 to 1 as needed
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def make_state(game: Dict[str, Any]) -> GameState:
    """Build a GameState response from a game dict."""
    p = game["player_hand"]
    d = game["dealer_hand"]
    return GameState(
        player_hand=p,
        dealer_hand=d,
        player_total=hand_total(p),
        dealer_total=hand_total(d),
        bet=game["bet"],
        status=game["status"]
    )


def dealer_play(game: Dict[str, Any]):
    """Dealer hits until 17+."""
    while hand_total(game["dealer_hand"]) < 17:
        game["dealer_hand"].append(draw(game["deck"]))


def resolve(game: Dict[str, Any]):
    """Set final status if player hasn't busted."""
    p = hand_total(game["player_hand"])
    d = hand_total(game["dealer_hand"])
    if d > 21:
        game["status"] = "dealer_bust"
    elif p > d:
        game["status"] = "player_win"
    elif p < d:
        game["status"] = "dealer_win"
    else:
        game["status"] = "push"


# ----- Endpoints -----
@app.get("/")
def root():
    return {"message": "Blackjack API is running"}

@app.post("/blackjack/start", response_model=GameState)
def start(req: StartRequest, x_user_id: str = Header(...)):
    if req.bet <= 0:
        raise HTTPException(status_code=400, detail="Bet must be > 0")

    deck = new_deck()
    player = [draw(deck), draw(deck)]
    dealer = [draw(deck), draw(deck)]

    game = {
        "deck": deck,
        "player_hand": player,
        "dealer_hand": dealer,
        "bet": req.bet,
        "status": "in_progress"
    }

    # Optional quick blackjack check
    p_total = hand_total(player)
    d_total = hand_total(dealer)
    if p_total == 21 and d_total == 21:
        game["status"] = "push"
    elif p_total == 21:
        game["status"] = "player_win"
    elif d_total == 21:
        game["status"] = "dealer_win"

    set_game(x_user_id, game)
    return make_state(game)

@app.post("/blackjack/hit", response_model=GameState)
def hit(x_user_id: str = Header(...)):
    game = get_game(x_user_id)
    if game["status"] != "in_progress":
        raise HTTPException(status_code=400, detail=f"Round is not active: {game['status']}")

    game["player_hand"].append(draw(game["deck"]))

    if hand_total(game["player_hand"]) > 21:
        game["status"] = "player_bust"

    return make_state(game)

@app.post("/blackjack/stand", response_model=GameState)
def stand(x_user_id: str = Header(...)):
    game = get_game(x_user_id)
    if game["status"] != "in_progress":
        raise HTTPException(status_code=400, detail=f"Round is not active: {game['status']}")

    dealer_play(game)
    resolve(game)
    return make_state(game)

@app.get("/blackjack/state", response_model=GameState)
def get_state(x_user_id: str = Header(...)):
    game = get_game(x_user_id)
    return make_state(game)
