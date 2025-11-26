
import pygame
from game import Game
from ui.menu import BunkerMenu

if __name__ == "__main__":
    pygame.init()
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h

    #screen_width = 1200
    #screen_height = screen_width / (16 / 9)

    base_width = 2560
    base_height = 1440
    displaySize = screen_width / base_width

    menu = BunkerMenu(screen_width, screen_height, displaySize)
    menu_result = menu.run()

    if menu_result == "start_game":
        game = Game(screen_width, screen_height, displaySize, zoom_level=1.0)
        game.run()
    else:
        print("Exiting game")


