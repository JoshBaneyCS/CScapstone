# 🃏 Blackjack FastAPI Backend

This project implements a RESTful Blackjack game backend using FastAPI.
It provides API endpoints to start a game, draw cards, stand, and retrieve
the current game state.

This backend is part of the CMSC 495 Capstone Project.

---

## Technologies Used

- Python 3
- FastAPI
- Uvicorn
- Pydantic

---

## Project Structure

blackjack-api/
- main.py
- README.md

---

## Running the Server Locally

### 1. Navigate to the backend directory

From the root of the repository:

python -m pip install fastapi uvicorn

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

POST /blackjack/start
Starts a new Blackjack game.

POST /blackjack/hit
Deals one card to the player.

POST /blackjack/stand
Ends the player’s turn and resolves the dealer’s hand.

GET /blackjack/state
Returns the current game state.

---

## Game State

The API tracks:
- Player hand and total
- Dealer hand and total
- Game status (in progress, win, bust, push)

---

## Notes

- Game state is stored in memory
- Designed for easy frontend integration
- Can be extended with authentication and persistence

---

## Author

Alan Becerra  
CMSC 495 Capstone Project
