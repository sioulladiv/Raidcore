
import pygame
from game import Game
from ui.menu import BunkerMenu

if __name__ == "__main__":
    pygame.init()
    info = pygame.display.Info()
    # get screen dimensions for scaling for later
    screen_width: int = info.current_w
    screen_height: int = info.current_h

    #screen size of pc used to design game
    base_width: int = 2560
    base_height: int = 1440
    displaySize: float = screen_width / base_width
    #initialise menu and run it, then start the game if the player selects "Start Game"
    menu = BunkerMenu(screen_width, screen_height, displaySize)
    menu_result = menu.run()

    if menu_result == "start_game":
        game = Game(screen_width, screen_height, displaySize, zoom_level=1.0)
        game.run()
    else:
        print("Exiting game")


