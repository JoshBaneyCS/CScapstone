from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
from typing import List, Dict, Any, Optional

app = FastAPI(title="Blackjack API")

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

# ----- In-memory game state (1 game for now) -----
GAME: Optional[Dict[str, Any]] = None

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

def state() -> GameState:
    global GAME
    if GAME is None:
        raise HTTPException(status_code=400, detail="No active round. Call /blackjack/start first.")
    p = GAME["player_hand"]
    d = GAME["dealer_hand"]
    return GameState(
        player_hand=p,
        dealer_hand=d,
        player_total=hand_total(p),
        dealer_total=hand_total(d),
        bet=GAME["bet"],
        status=GAME["status"]
    )

def dealer_play():
    """Dealer hits until 17+."""
    global GAME
    while hand_total(GAME["dealer_hand"]) < 17:
        GAME["dealer_hand"].append(draw(GAME["deck"]))

def resolve():
    """Set final status if player hasn't busted."""
    global GAME
    p = hand_total(GAME["player_hand"])
    d = hand_total(GAME["dealer_hand"])
    if d > 21:
        GAME["status"] = "dealer_bust"
    elif p > d:
        GAME["status"] = "player_win"
    elif p < d:
        GAME["status"] = "dealer_win"
    else:
        GAME["status"] = "push"

# ----- Endpoints -----
@app.get("/")
def root():
    return {"message": "Blackjack API is running"}

@app.post("/blackjack/start", response_model=GameState)
def start(req: StartRequest):
    global GAME
    if req.bet <= 0:
        raise HTTPException(status_code=400, detail="Bet must be > 0")

    deck = new_deck()
    player = [draw(deck), draw(deck)]
    dealer = [draw(deck), draw(deck)]

    GAME = {
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
        GAME["status"] = "push"
    elif p_total == 21:
        GAME["status"] = "player_win"
    elif d_total == 21:
        GAME["status"] = "dealer_win"

    return state()

@app.post("/blackjack/hit", response_model=GameState)
def hit():
    global GAME
    s = state()
    if s.status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Round is not active: {s.status}")

    GAME["player_hand"].append(draw(GAME["deck"]))

    if hand_total(GAME["player_hand"]) > 21:
        GAME["status"] = "player_bust"

    return state()

@app.post("/blackjack/stand", response_model=GameState)
def stand():
    global GAME
    s = state()
    if s.status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Round is not active: {s.status}")

    dealer_play()
    resolve()
    return state()

@app.get("/blackjack/state", response_model=GameState)
def get_state():
    return state()
