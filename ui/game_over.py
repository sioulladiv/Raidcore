"""Game Over screen with Restart / Quit buttons."""
import pygame
import sys


class GameOverScreen:
    """Full-screen overlay shown when the player dies.

    Displays a title, a taunting message based on the level reached, and
    two buttons (Restart / Quit) that respond to both keyboard and mouse.
    """
    def __init__(self, screen_width: int, screen_height: int) -> None:
        """Create the game-over screen.

        Args:
            screen_width: Screen width in pixels.
            screen_height: Screen height in pixels.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 72)

        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)        
        self.button_width = 300
        self.button_height = 60
        self.button_spacing = 20
        self.restart_button = pygame.Rect(0, 0, self.button_width, self.button_height)
        self.quit_button = pygame.Rect(0, 0, self.button_width, self.button_height)
        self._refresh_layout(screen_width, screen_height)
        
        self.selected_button = 0 

    def _refresh_layout(self, screen_width: int, screen_height: int) -> None:
        """Update button positions for the current window size."""
        self.screen_width = screen_width
        self.screen_height = screen_height

        centerX = self.screen_width // 2
        centerY = self.screen_height // 2

        self.restart_button = pygame.Rect(
            centerX - self.button_width // 2,
            centerY + 50,
            self.button_width,
            self.button_height
        )

        self.quit_button = pygame.Rect(
            centerX - self.button_width // 2,
            centerY + 50 + self.button_height + self.button_spacing,
            self.button_width,
            self.button_height
        )
        
    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        """Process pygame events and return an action string.
        Args:
            events: List of ``pygame.event.Event`` objects to process.

        Returns:
            ``'restart'``, ``'quit'``, or ``None`` when no action is taken.
        """

        display_surface = pygame.display.get_surface()
        if display_surface is not None:
            self._refresh_layout(display_surface.get_width(), display_surface.get_height())

        # Handle keyboard navigation and selection
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_button = 0
                elif event.key == pygame.K_DOWN:
                    self.selected_button = 1

                # Enter or Space activates the selected button
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.selected_button == 0:
                        return "restart"
                    else:
                        return "quit"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"

            #handle mouse movement to update selected button and click to activate
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                if self.restart_button.collidepoint(mouse_pos):
                    self.selected_button = 0
                elif self.quit_button.collidepoint(mouse_pos):
                    self.selected_button = 1
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    mouse_pos = event.pos
                    if self.restart_button.collidepoint(mouse_pos):
                        return "restart"
                    elif self.quit_button.collidepoint(mouse_pos):
                        return "quit"
        return None

    def draw(self, screen: pygame.Surface, level: int) -> None:
        """Render the game-over overlay onto *screen*.

        Args:
            screen: The main display surface.
            level: Current level index, used to pick the taunting message.
        """
        self._refresh_layout(screen.get_width(), screen.get_height())

        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        game_over_text = self.font_large.render("GAME OVER", True, (255, 0, 0))
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

        instruction_text = self.font_small.render(message, True,(255, 255, 255))
        instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 30))
        screen.blit(instruction_text, instruction_rect)
    
        # Draw buttons with highlight on selected
        restart_color = (255, 255, 255) if self.selected_button == 0 else (128, 128, 128)
        restart_bg_color = (64, 64, 64) if self.selected_button == 0 else (0, 0, 0)

        pygame.draw.rect(screen, restart_bg_color, self.restart_button)
        pygame.draw.rect(screen, restart_color, self.restart_button, 3)
        restart_text = self.font_medium.render("RESTART", True, restart_color)
        restart_text_rect = restart_text.get_rect(center=self.restart_button.center)
        screen.blit(restart_text, restart_text_rect)
        
        quit_color = (255, 255, 255) if self.selected_button == 1 else (128, 128, 128)
        quit_bg_color = (64, 64, 64) if self.selected_button == 1 else (0, 0, 0)
        pygame.draw.rect(screen, quit_bg_color, self.quit_button)
        pygame.draw.rect(screen, quit_color, self.quit_button, 3)
        quit_text = self.font_medium.render("QUIT", True, quit_color)
        quit_text_rect = quit_text.get_rect(center=self.quit_button.center)
        screen.blit(quit_text, quit_text_rect)
