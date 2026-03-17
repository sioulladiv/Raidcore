"""Dynamic torch-light effect with warm colour gradient."""
from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.player import Player
    from world.camera import Camera


class Lighting:
    """
    Renders a radial vignette affect around the player to simulate torch light.

    A warm gradient surface is blended over a dark overlay each frame.
    The gradient is only regenerated when darkness changes.
    """
    def __init__(self, radius: int, darkness: int = 210) -> None:
        """
        Create Lighting instance.

        Args:
            radius: Initial light radius in world pixels.
            darkness: Alpha value of the dark overlay (0–255)
                make the unlit areas darker (default 210).
        """
        self.radius = radius

        self.darkness = darkness
        self.last_darkness = darkness
        
        # Cache the light gradient surface
        self.surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        self._regenerate_light_surface()
        
        
        # Pre-create dark overlay surface to reuse
        self.dark_overlay = None

        self.last_screen_size = (0, 0)

    def _regenerate_light_surface(self) -> None:
        """Regenerate the light gradient surface."""
        import pygame.surfarray as surfarray
        
        self.surface.fill((0, 0, 0, 0))
        
        # Get pixel arrays for direct manipulation which is faster than drawing
        pixels = surfarray.pixels3d(self.surface)
        alphas = surfarray.pixels_alpha(self.surface)
        
        center = self.radius
        
        for y in range(self.radius* 2):
            for x in range(self.radius* 2):
                dx = x - center
                dy = y - center
                dist = (dx*dx + dy*dy)**0.5
                
                if dist <= self.radius:
                    ratio = dist / self.radius  # 0 at center 1 at edge
                    
                    # Quadratic falloff for smooth gradient                       
                    
                    pixels[x, y, 0] = int(255*(1-ratio*0.2))
                    pixels[x, y, 1] = int(200 - ratio * 50)
                    pixels[x, y, 2] = int(100 - ratio * 80)
                    alphas[x, y] = int(( (1 - ratio)**2)*self.darkness)

    def update(self, player: Player, camera: Camera, darkness: int = 210) -> None:
        """
        Recompute the light position each frame.

        Args:
            player: Player entity whose centre is used as the light source.
            camera: Active camera for world–to–screen projection.
            darkness: Target darkness override (default 210).

        """
        # Only regenerate if darkness changed

        if self.darkness!=darkness:
            self.darkness = darkness
            
            # Recreate surface if size changed
            if self.surface.get_width() != self.radius*2:
                self.surface = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            self._regenerate_light_surface()



        player_center_x= player.x+ (player.width/2)
        player_center_y= player.y +(player.height/2)
        
        self.x = player_center_x*camera.zoom + camera.offset_x
        self.y = player_center_y*camera.zoom + camera.offset_y
        
    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """
        Blit the dark overlay (with the light hole cut out) onto surface.

        Args:
            surface: main display surface
            camera: Active camera
        """
        screen_size = (surface.get_width(), surface.get_height())
        
        # Only recreate dark_overlay if screen size changed
        if self.dark_overlay is None or self.last_screen_size != screen_size:
            self.dark_overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
            self.last_screen_size = screen_size
        
        #reuse the surface instead of creating new one
        self.dark_overlay.fill((0, 0, 0, self.darkness))
        
        center_x = self.x
        center_y = self.y
        
        self.dark_overlay.blit(self.surface, (center_x - self.radius, center_y - self.radius), special_flags=pygame.BLEND_RGBA_SUB)
        
        surface.blit(self.dark_overlay, (0, 0))