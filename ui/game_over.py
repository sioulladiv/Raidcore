import pygame
import sys

class GameOverScreen:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        self.red = (255, 0, 0)
        self.white = (255, 255, 255)
        self.gray = (128, 128, 128)
        self.dark_gray = (64, 64, 64)
        self.black = (0, 0, 0)
        
        self.button_width = 300
        self.button_height = 60
        self.button_spacing = 20
        
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        self.restart_button = pygame.Rect(
            center_x - self.button_width // 2,
            center_y + 50,
            self.button_width,
            self.button_height
        )
        
        self.quit_button = pygame.Rect(
            center_x - self.button_width // 2,
            center_y + 50 + self.button_height + self.button_spacing,
            self.button_width,
            self.button_height
        )
        
        self.selected_button = 0 
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_button = 0
                elif event.key == pygame.K_DOWN:
                    self.selected_button = 1
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.selected_button == 0:
                        return "restart"
                    else:
                        return "quit"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                if self.restart_button.collidepoint(mouse_pos):
                    self.selected_button = 0
                elif self.quit_button.collidepoint(mouse_pos):
                    self.selected_button = 1
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    mouse_pos = pygame.mouse.get_pos()
                    if self.restart_button.collidepoint(mouse_pos):
                        return "restart"
                    elif self.quit_button.collidepoint(mouse_pos):
                        return "quit"
        return None

    def draw(self, screen, level):
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill(self.black)
        screen.blit(overlay, (0, 0))
        
        game_over_text = self.font_large.render("GAME OVER", True, self.red)
        game_over_rect = game_over_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 100))
        screen.blit(game_over_text, game_over_rect)
        if level < 3:
            message = f"The quit button is just there"
        elif level < 4: 
            message = "Three whole levels. Slow down, champ, you’re scaring me."
        elif level < 5:
            message = "Read the tutorial again."
        elif level < 6:
            message = "Seriously, just read the tutorial."
        elif level < 7:
            message = "Not bad. Almost like you know what you’re doing."

        instruction_text = self.font_small.render(message, True, self.white)
        instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 30))
        screen.blit(instruction_text, instruction_rect)
        
        restart_color = self.white if self.selected_button == 0 else self.gray
        restart_bg_color = self.dark_gray if self.selected_button == 0 else self.black
        pygame.draw.rect(screen, restart_bg_color, self.restart_button)
        pygame.draw.rect(screen, restart_color, self.restart_button, 3)
        restart_text = self.font_medium.render("RESTART", True, restart_color)
        restart_text_rect = restart_text.get_rect(center=self.restart_button.center)
        screen.blit(restart_text, restart_text_rect)
        
        quit_color = self.white if self.selected_button == 1 else self.gray
        quit_bg_color = self.dark_gray if self.selected_button == 1 else self.black
        pygame.draw.rect(screen, quit_bg_color, self.quit_button)
        pygame.draw.rect(screen, quit_color, self.quit_button, 3)
        quit_text = self.font_medium.render("QUIT", True, quit_color)
        quit_text_rect = quit_text.get_rect(center=self.quit_button.center)
        screen.blit(quit_text, quit_text_rect)
