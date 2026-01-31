from game import Game

g = Game()
g.is_playing = True
while g.is_running:
    g.game_loop()