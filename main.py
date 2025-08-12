from game import Game
from ui.menu import BunkerMenu

if __name__ == "__main__":
    menu = BunkerMenu(2560, 1440)
    menu_result = menu.run()
    
    if menu_result == "start_game":
        game = Game(2560, 1440, zoom_level=1.0)
        game.run()
    else: 
        print("Exiting game")