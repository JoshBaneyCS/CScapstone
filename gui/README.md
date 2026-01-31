# 🃏 Blackjack FastAPI Backend

This project implements a GUI for the Capstone Casino game. It (will) connect to the backend API's for user authentication, bank roll and all casino games.
It is part of the front-end for CMSC495 Capstone Project.

---

## Technologies Used

- Python 3.10+
- Pygame 2.6.1
- PyGame-Gui 0.6.14

---

## Project Structure

gui/
- main.py
- game.py
- menu.py
- README.md

---

## Running the Application Locally

### 1. Navigate to the gui directory

From the root of the repository:

python -m pip install pygame pygame-gui

### 2. Start the application

python main.py

The application should run and the login screen should appear

## GUI

The application currently provides a GUI for the game that:
- Allows the user to login or exit
- Choose a game to play

The application will (soon) provide a GUI for:
- playing poker/blackjack
- create/update user account information

---

## Notes

- Still needs to be integrated with back end systems
- Will create theming JSON files for pygame-gui to make it look pretty after integration with backend is complete 
- same with Audio?

---

## Author

Jerry Gardiner  
CMSC 495 Capstone Project
