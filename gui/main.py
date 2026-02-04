from game import Game

game = Game()
game.is_playing = True

while game.is_running:
    game.game_loop()
