import pygame
import sys

class BunkerMenu:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Dungeon Escape - Main Menu")

        self.menu_options = ["Start Game", "Controls", "Credits", "Exit"]
        self.selected_option = 0

        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gray = (128, 128, 128)
        self.dark_gray = (64, 64, 64)
        self.red = (255, 0, 0)
        self.blue = (100, 150, 255)

        self.title_font = pygame.font.Font(None, 96)
        self.subtitle_font = pygame.font.Font(None, 48)
        self.menu_font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 32)

        self.button_width = 350
        self.button_height = 70
        self.button_spacing = 20

        center_x = screen_width // 2
        start_y = screen_height // 2 - 50
        
        self.buttons = []
        for i in range(len(self.menu_options)):
            button_rect = pygame.Rect(
                center_x - self.button_width // 2,
                start_y + i * (self.button_height + self.button_spacing),
                self.button_width,
                self.button_height
            )
            self.buttons.append(button_rect)

        self.clock = pygame.time.Clock()
        
        self.show_controls = False
        self.show_credits = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if self.show_controls or self.show_credits:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.show_controls = False
                        self.show_credits = False
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.handle_selection()
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            elif event.type == pygame.MOUSEMOTION:
                if not (self.show_controls or self.show_credits):
                    mouse_pos = pygame.mouse.get_pos()
                    for i, button in enumerate(self.buttons):
                        if button.collidepoint(mouse_pos):
                            self.selected_option = i
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not (self.show_controls or self.show_credits):
                    mouse_pos = pygame.mouse.get_pos()
                    for i, button in enumerate(self.buttons):
                        if button.collidepoint(mouse_pos):
                            self.selected_option = i
                            return self.handle_selection()
                elif event.button == 1 and (self.show_controls or self.show_credits):
                    # Close info screens with mouse click
                    self.show_controls = False
                    self.show_credits = False
        return None

    def handle_selection(self):
        selected = self.menu_options[self.selected_option]
        if selected == "Start Game":
            return "start_game"
        elif selected == "Controls":
            self.show_controls = True
            return None
        elif selected == "Credits":
            self.show_credits = True
            return None
        elif selected == "Exit":
            return "quit"

    def draw_info_screen(self, title, content_lines):
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill(self.black)
        self.screen.blit(overlay, (0, 0))
        
        box_width = 800
        box_height = 600
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2
        
        info_box = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, self.dark_gray, info_box)
        pygame.draw.rect(self.screen, self.white, info_box, 3)
        
        title_text = self.subtitle_font.render(title, True, self.blue)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, box_y + 60))
        self.screen.blit(title_text, title_rect)
        
        start_y = box_y + 120
        for i, line in enumerate(content_lines):
            text = self.small_font.render(line, True, self.white)
            text_rect = text.get_rect(center=(self.screen_width // 2, start_y + i * 40))
            self.screen.blit(text, text_rect)
        
        close_text = self.small_font.render("Press ESC or ENTER to close", True, self.gray)
        close_rect = close_text.get_rect(center=(self.screen_width // 2, box_y + box_height - 40))
        self.screen.blit(close_text, close_rect)

    def draw(self):
        self.screen.fill(self.black)

        title_shadow = self.title_font.render("DUNGEON ESCAPE", True, self.dark_gray)
        title_shadow_rect = title_shadow.get_rect(center=(self.screen_width // 2 + 3, 203))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title_text = self.title_font.render("DUNGEON ESCAPE", True, self.red)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title_text, title_rect)

        subtitle_text = self.subtitle_font.render("Survive the depths", True, self.white)
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, 280))
        self.screen.blit(subtitle_text, subtitle_rect)

        nav_text = self.small_font.render("Use arrow keys or mouse to navigate", True, self.gray)
        nav_rect = nav_text.get_rect(center=(self.screen_width // 2, 350))
        self.screen.blit(nav_text, nav_rect)

        for i, (option, button_rect) in enumerate(zip(self.menu_options, self.buttons)):
            button_color = self.white if i == self.selected_option else self.gray
            button_bg_color = self.dark_gray if i == self.selected_option else self.black
            
            pygame.draw.rect(self.screen, button_bg_color, button_rect)
            pygame.draw.rect(self.screen, button_color, button_rect, 3)
            
            text_surface = self.menu_font.render(option, True, button_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)

        if self.show_controls:
            controls_content = [
                "Pretty self explanatory",
                "WASD or Arrow Keys to Move player",
                "",
                "Use the mouse to aim weapon",
                "Left Click to Shoot.",
                "What else did you expect lil bro",
                "",
                "E - Interact with chests",
                ""
            ]
            self.draw_info_screen("CONTROLS", controls_content)
            
        elif self.show_credits:
            credits_content = [
                "DUNGEON ESCAPE",
                "",
                "Developed by: only the best"

            ]
            self.draw_info_screen("CREDITS", credits_content)

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