# 🃏 Texas Hold 'Em FastAPI Backend

This project implements a RESTful Texas Hold 'Em game backend using FastAPI.
It provides API endpoints to start a game, run the flop, turn, river, and showdown, and run a test/{win_needed} function.
This backend is part of the CMSC 495 Capstone Project.

---

## Technologies Used

- Python 3
- FastAPI
- Uvicorn
- Pydantic

---

## Project Structure

apps/
- main.py
- README.md

---

## Running the Server Locally

### 1. Navigate to the backend directory

From the root of the repository:

python -m pip install fastapi uvicorn pydantic

### 2. Start the server

python -m uvicorn main:app --reload

When running, the server will be available at:

http://127.0.0.1:8000

---

## API Documentation

FastAPI automatically generates interactive documentation.

Open your browser and go to:

http://127.0.0.1:8000/docs

---

## API Endpoints

GET /
Returns a message confirming the API is running.

POST /texas/old_start
Starts a new (simplified) Texas Hold 'Em game, dealing 2 cards to each player.

POST /texas/single/start
Initiates a new single-player Texas Hold 'Em game. Starts pre-flop betting with /texas/single/bet.

POST /texas/single/bet
Place the initial bet for a betting round.

POST /texas/single/action
Player action: stay (check/call), raise, or fold.

POST /texas/flop
Deals the flop (3 to the community)

POST /texas/turn
Deals the flop (3 to the community)

POST /texas/river
Deals the river (1 to the community)

POST /texas/showdown
Finishes the game, revealing all cards.

POST /texas/test/{win_needed}
Runs games repeatedly until the winning hand's number (via evaluate_best_hand) matches the win_needed

GET /texas/state
Returns the current game state.

---

## Game State

The API tracks:
- Players' hands
- Community sards
- Game status (preflop, flop, turn, river, showdown, finished)
- Bet
- Winning hand rank number
- Winners

---

## Notes

- Game state is stored in memory
- Designed for easy frontend integration
- Can be extended with authentication and persistence

---

## Author

David Czolba
CMSC 495 Capstone Project
Kindly ripped off from Alan Becerra's Blackjack
