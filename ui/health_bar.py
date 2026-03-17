"""Player health-bar HUD element drawn above the player sprite."""
from __future__ import annotations

import pygame


from entities.player import Player
from world.camera import Camera


class HealthBar:
    """Renders a health bar directly above the player sprite.

    The bar anchors itself to the player's world position each frame so it
    moves with the player as the camera pans/zooms.
    """

    def __init__(self, x: float, y: float, width: int, height: int, displaySize: float) -> None:
        """Create a HealthBar.

        Args:
            x: Initial screen x-coordinate (recalculated each draw call).
            y: Initial screen y-coordinate (recalculated each draw call).
            width: Base bar width before display scaling.
            height: Base bar height before display scaling.
            displaySize: Scaling ratio (screen_width / 2560).
        """
        self.x = x
        self.y = y
        self.width = width *2
        self.height = height
        self.displaySize = displaySize

        self.life = 100

        self.border_color = (68, 29, 23)
        self.secondary_border = (241, 210, 205)
        self.background_color = (0, 0, 0)

        self.fill_color = (218, 77, 56)
        self.borderthickness = max(1, int(self.height * 0.07))

    def update(self, life: float) -> None:
        """Set the current health percentage (0–100).

        Args:
            life: Health value; clamped to [0, 100].
        """
        self.life = max(0, min(100, int(life)))

    def damage(self, damage_amount: float) -> None:
        """Reduce health by *damage_amount*.

        Args:
            damage_amount: Raw damage to subtract (clamped at 0).
        """
        self.update(self.life - damage_amount)

    def update_animation(self, dt: float) -> None:
        """Reserved for future animation logic; currently a no-op.

        Args:
            dt: Delta time in milliseconds.
        """
        pass

    def draw(self, screen: pygame.Surface, player: Player, camera: Camera) -> None:
        """Render the health bar above the player.

        The bar is repositioned to track the player's world position each
        call, so no separate update step is needed.

        Args:
            screen: The main display surface.
            player: Player entity whose position anchors the bar.
            camera: Active camera for world–to–screen projection.
        """
        zoom = camera.zoom
        
        # Calculate scaled dimensions
        scaled_width = self.width *zoom
        scaled_height = self.height * zoom
        scaled_border = max(1, int(self.borderthickness* zoom))
        
        # Position health bar centered above player's head
        self.x = (player.x + player.width / 2)*zoom + camera.offset_x-scaled_width / 2
        self.y = (player.y-15)*zoom + camera.offset_y +180
        
        outer1 =pygame.Rect(self.x, self.y,scaled_width, scaled_height  )
        pygame.draw.rect(screen, self.border_color, outer1, scaled_border)

        inner_x = self.x + scaled_border
        inner_y = self.y + scaled_border

        inner_width = max(0, scaled_width - 2*scaled_border)
        inner_hight = max(0, scaled_height - 2*scaled_border)

        inner_bg = pygame.Rect(inner_x, inner_y, inner_width, inner_hight)

        pygame.draw.rect(screen, self.background_color, inner_bg)

        # Draw the filled portion of the health bar based on current life percentage
        fill_w = int(inner_width * (self.life / 100.0))
        if fill_w > 0:
            fill_rect = pygame.Rect(inner_x, inner_y, fill_w, inner_hight)
            pygame.draw.rect(screen, self.fill_color, fill_rect)
