import pygame


class ExperienceBar:
    """Vertical experience bar displayed in the bottom-right corner of the screen.

    Fills from the bottom upward as the player accumulates XP.
    """

    def __init__(self, x: float, y: float, width: int, height: int, displaySize: float) -> None:
        """Create an ExperienceBar.

        Args:
            x: Screen x-coordinate of the bar's top-left corner.
            y: Screen y-coordinate of the bar's top-left corner.
            width: Bar width in pixels before scaling.
            height: Bar height in pixels before scaling.
            displaySize: Scaling ratio (screen_width / 2560).
        """
        self.x = x
        self.y = y
        self.width = width *2

        self.height = height

        self.displaySize = displaySize

        self.experience = 100

        
        self.border_thickness = max(1, int(self.height * 0.07))

    def update(self, experience: float) -> None:
        """Set the current XP fill level (0–100).
        Args:
            experience: XP value; clamped to [0, 100].
        """
        self.experience = max(0, min(100, int(experience)))

    def update_animation(self, dt: float) -> None:
        """Reserved for future animation logic; currently a no-op.
        Args:
            dt: Delta time in milliseconds.
        """
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render the experience bar at its fixed screen position.

        Args:
            screen: The main display surface.
        """
        outer1 = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (200, 200, 200), outer1, self.border_thickness)

        inner_x = self.x + self.border_thickness

        inner_y = self.y + self.border_thickness

        inner_w = max(0, self.width - 2 * self.border_thickness)
        inner_h = max(0, self.height - 2 * self.border_thickness)

        inner_bg = pygame.Rect(inner_x, inner_y, inner_w, inner_h)
        pygame.draw.rect (screen, (0, 0, 0), inner_bg)

        fill_h = int(inner_h*(self.experience / 100.0))
        if fill_h > 0:
            fill_y = inner_y + inner_h-fill_h  

            fill_rect = pygame.Rect(inner_x, fill_y, inner_w, fill_h)
            pygame.draw.rect(screen, (150, 150, 150), fill_rect)
