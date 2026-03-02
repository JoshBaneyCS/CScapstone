import asyncio
import sys
import pygame
import pygame_gui

try:
    from game import Game

    # Initialize the main game GUI
    game = Game()

    # Set the initial state to begin the game loop.
    game.is_playing = True
    print("Game initialized successfully", flush=True)

except Exception as e:
    print(f"ERROR initializing game: {e}", flush=True)
    import traceback
    traceback.print_exc()
    if sys.platform == "emscripten":
        from platform import window
        window.infobox.style.display = "block"
        window.infobox.innerText = f"Error: {e}"
    raise


async def main():
    """Async main loop required by pygbag for browser-native rendering.

    Each iteration processes one frame and yields to the browser event loop
    via asyncio.sleep(0), allowing the browser to handle rendering and input.
    """
    while game.is_running:
        game.game_loop_tick()
        await asyncio.sleep(0)


asyncio.run(main())
