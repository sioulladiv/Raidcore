import pygame
import sys
import os
from config.game_settings import game_settings

class Slider:
    def __init__(self, x, y, width, height, default_value=50):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_value = 100
        self.value = default_value
        self.handle_width = 20
        self.handle_height = height + 10
        self.dragging = False
        
        self.track_color = (100, 100, 100)
        self.handle_color = (255, 255, 255)
        self.handle_hover_color = (200, 200, 200)

    def get_handle_x(self):
        return self.x + (self.width - self.handle_width) * (self.value / self.max_value)

    def update(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        handle_x = self.get_handle_x()
        handle_rect = pygame.Rect(handle_x, self.y - 5, self.handle_width, self.handle_height)
        
        if handle_rect.collidepoint(mouse_pos) or self.dragging:
            if mouse_pressed:
                self.dragging = True
                relative_x = mouse_pos[0] - self.x
                self.value = (relative_x / self.width) * self.max_value
                self.value = max(0, min(self.value, self.max_value))
        
        if not mouse_pressed:
            self.dragging = False
            
        self.draw(surface)

    def draw(self, surface):
        track_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.track_color, track_rect)
        
        handle_x = self.get_handle_x()
        handle_rect = pygame.Rect(handle_x, self.y - 5, self.handle_width, self.handle_height)
        
        mouse_pos = pygame.mouse.get_pos()
        color = self.handle_hover_color if handle_rect.collidepoint(mouse_pos) else self.handle_color
        
        pygame.draw.rect(surface, color, handle_rect)
        pygame.draw.rect(surface, (0, 0, 0), handle_rect, 2)  


class BunkerMenu:
    def __init__(self, screen_width, screen_height, displaySize):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.displaySize = displaySize
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Dungeon Escape - Main Menu")

        self.menu_options = ["Start Game", "Controls", "Settings", "Credits", "Exit"]
        self.selected_option = 0

        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gray = (128, 128, 128)
        self.dark_gray = (64, 64, 64)
        self.red = (255, 0, 0)
        self.blue = (100, 150, 255)

        self.full_path_font = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Assets", "Fonts", "minecraft_font.ttf")


        self.title_font = pygame.font.Font(self.full_path_font, int(96 * self.displaySize))
        self.subtitle_font = pygame.font.Font(self.full_path_font, int(48 * self.displaySize))
        self.menu_font = pygame.font.Font(self.full_path_font, int(42 * self.displaySize))
        self.small_font = pygame.font.Font(self.full_path_font, int(32 * self.displaySize))

        self.button_width = int(350 * self.displaySize)
        self.button_height = int(70 * self.displaySize)
        self.button_spacing = int(20 * self.displaySize)

        self.sliders = []

        self.masterVolume_slider = Slider(
            x=screen_width // 2 - 150,
            y=screen_height // 2 + 150,
            width=300,
            height=20,
            default_value=game_settings.settings["master_volume"]
        )
        self.musicVolume_slider = Slider(
            x=screen_width // 2 - 150,
            y=screen_height // 2 + 270,
            width=300,
            height=20,
            default_value=game_settings.settings["music_volume"]
        )
        self.SFXVolume_slider = Slider(
            x=screen_width // 2 - 150,
            y=screen_height // 2 + 390,
            width=300,
            height=20,
            default_value=game_settings.settings["sfx_volume"]
        )

        self.sliders.append(self.masterVolume_slider)
        self.sliders.append(self.musicVolume_slider)
        self.sliders.append(self.SFXVolume_slider)

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
        self.show_settings = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if self.show_controls or self.show_credits or self.show_settings:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        # Save settings when closing settings screen
                        if self.show_settings:
                            game_settings.update_from_sliders(
                                self.masterVolume_slider,
                                self.musicVolume_slider,
                                self.SFXVolume_slider
                            )
                        self.show_controls = False
                        self.show_credits = False
                        self.show_settings = False
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.handle_selection()
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            elif event.type == pygame.MOUSEMOTION:
                if not (self.show_controls or self.show_credits or self.show_settings):
                    mouse_pos = pygame.mouse.get_pos()
                    for i, button in enumerate(self.buttons):
                        if button.collidepoint(mouse_pos):
                            self.selected_option = i
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not (self.show_controls or self.show_credits or self.show_settings):
                    mouse_pos = pygame.mouse.get_pos()
                    for i, button in enumerate(self.buttons):
                        if button.collidepoint(mouse_pos):
                            self.selected_option = i
                            return self.handle_selection()
                elif event.button == 1 and (self.show_controls or self.show_credits):
                    self.show_controls = False
                    self.show_credits = False
        
        if self.show_settings:
            for slider in self.sliders:
                slider.update(self.screen)
        
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
        elif selected == "Settings":
            self.show_settings = True
            return None
        elif selected == "Exit":
            return "quit"

    def draw_info_screen(self, title, content_lines):
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill(self.black)
        self.screen.blit(overlay, (0, 0))
        
        box_width = 800*self.displaySize
        box_height = 600*self.displaySize
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2
        
        info_box = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, self.dark_gray, info_box)
        pygame.draw.rect(self.screen, self.white, info_box, 3)
        
        title_text = self.subtitle_font.render(title, True, self.blue)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, box_y + 60*self.displaySize))
        self.screen.blit(title_text, title_rect)

        start_y = box_y + 120*self.displaySize
        for i, line in enumerate(content_lines):
            text = self.small_font.render(line, True, self.white)
            text_rect = text.get_rect(center=(self.screen_width // 2, start_y + i * 40*self.displaySize))
            self.screen.blit(text, text_rect)
        
        close_text = self.small_font.render("Press ESC or ENTER to close", True, self.gray)
        close_rect = close_text.get_rect(center=(self.screen_width // 2, box_y + box_height - 40*self.displaySize))
        self.screen.blit(close_text, close_rect)

    def draw(self):
        self.screen.fill(self.black)

        title_shadow = self.title_font.render("DUNGEON ESCAPE", True, self.dark_gray)
        title_shadow_rect = title_shadow.get_rect(center=(self.screen_width // 2 + 3, 203))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title_text = self.title_font.render("DUNGEON ESCAPE", True, self.red)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title_text, title_rect)

        for i, (option, button_rect) in enumerate(zip(self.menu_options, self.buttons)):
            text_color = self.white if i == self.selected_option else self.gray
            
            if i == self.selected_option: arrow_text = ">"
            else: arrow_text = ""

            text_surface = self.menu_font.render(f"{arrow_text} {option}", True, text_color)
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
                "Developed by: ludovailis"

            ]
            self.draw_info_screen("CREDITS", credits_content)

        elif self.show_settings:
            self.draw_settings_screen()

    def draw_settings_screen(self):
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
        
        title_text = self.subtitle_font.render("SETTINGS", True, self.blue)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, box_y + 60))
        self.screen.blit(title_text, title_rect)
        
        labels = ["Master Volume", "Music Volume", "SFX Volume"]
        start_y = box_y + 150
        
        for i, (label, slider) in enumerate(zip(labels, self.sliders)):
            label_text = self.small_font.render(f"{label}: {int(slider.value)}%", True, self.white)
            label_rect = label_text.get_rect(center=(self.screen_width // 2, start_y + i * 120))
            self.screen.blit(label_text, label_rect)
            
            slider.y = start_y + i * 120 + 30
            slider.draw(self.screen)
        
        close_text = self.small_font.render("Press ESC or ENTER to close", True, self.gray)
        close_rect = close_text.get_rect(center=(self.screen_width // 2, box_y + box_height - 40))
        self.screen.blit(close_text, close_rect)

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
    menu = BunkerMenu(2560, 1440)
    result = menu.run()
    print(f"Menu result: {result}")
    sys.exit()