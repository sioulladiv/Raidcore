import pygame
import sys

class BunkerMenu:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Main Menu")

        self.menu_options = ["Start Game", "Continue", "Options", "Exit"]
        self.selected_option = 0

        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.selected_color = (100, 150, 255)

        self.title_font = pygame.font.Font(None, 72)
        self.menu_font = pygame.font.Font(None, 48)

        self.clock = pygame.time.Clock()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                elif event.key == pygame.K_RETURN:
                    return self.menu_options[self.selected_option].lower().replace(" ", "_")
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
        return None

    def draw(self):
        self.screen.fill(self.black)

        title_text = self.title_font.render("GAME MENU", True, self.white)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_text, title_rect)

        start_y = 300
        for i, option in enumerate(self.menu_options):
            y_pos = start_y + i * 60
            color = self.selected_color if i == self.selected_option else self.white
            prefix = "> " if i == self.selected_option else "  "
            text_surface = self.menu_font.render(prefix + option, True, color)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, y_pos))
            self.screen.blit(text_surface, text_rect)

    def run(self):
        while True:
            self.clock.tick(60)
            action = self.handle_events()
            if action:
                if action in ["quit", "exit"]:
                    break
                else:
                    return action
            self.draw()
            pygame.display.flip()
        pygame.quit()
        return "quit"

if __name__ == "__main__":
    menu = BunkerMenu(1280, 720)
    result = menu.run()
    print(f"Menu result: {result}")
    sys.exit()