
from game import Game

# Initialize the main game GUI
game = Game()

# Set the initial state to begin the game loop.
game.is_playing = True

# Main execution loop. This handles the high-level logic for keeping
# the application window open and active.
while game.is_running:
    # Executes the update/draw cycle for the currently active scene.
    game.game_loop()
