import asyncio

from game import Game

# Initialize the main game GUI
game = Game()

# Set the initial state to begin the game loop.
game.is_playing = True


async def main():
    """Async main loop required by pygbag for browser-native rendering.

    Each iteration processes one frame and yields to the browser event loop
    via asyncio.sleep(0), allowing the browser to handle rendering and input.
    """
    while game.is_running:
        game.game_loop_tick()
        await asyncio.sleep(0)


asyncio.run(main())
