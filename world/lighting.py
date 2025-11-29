import pygame
class Lighting:
    def __init__(self, radius, darkness=210):
        self.radius = radius
        self.darkness = darkness
        self.last_darkness = darkness
        
        # Cache the light gradient surface
        self.surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self._regenerate_light_surface()
        
        # Pre-create dark overlay surface to reuse
        self.dark_overlay = None
        self.last_screen_size = (0, 0)

    def _regenerate_light_surface(self):
        """Regenerate the light gradient surface (only when darkness changes)"""
        self.surface.fill((0, 0, 0, 0))  # Clear surface
        for r in range(self.radius):
            alpha = int((r / self.radius) * self.darkness)
            pygame.draw.circle(self.surface, (0, 255, 0, alpha), (self.radius, self.radius), self.radius - r)

    def update(self, player, camera, darkness=210):
        # Only regenerate if darkness changed
        if self.darkness != darkness:
            self.darkness = darkness
            self._regenerate_light_surface()

        player_center_x = player.x + (player.width / 2)
        player_center_y = player.y + (player.height / 2)
        
        self.x = player_center_x * camera.zoom + camera.offset_x
        self.y = player_center_y * camera.zoom + camera.offset_y
        
    def draw(self, surface, camera):
        screen_size = (surface.get_width(), surface.get_height())
        
        # Only recreate dark_overlay if screen size changed
        if self.dark_overlay is None or self.last_screen_size != screen_size:
            self.dark_overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
            self.last_screen_size = screen_size
        
        # Reuse the surface instead of creating new one
        self.dark_overlay.fill((0, 0, 0, self.darkness))
        
        center_x = self.x
        center_y = self.y
        
        self.dark_overlay.blit(self.surface, (center_x - self.radius, center_y - self.radius), special_flags=pygame.BLEND_RGBA_SUB)
        
        surface.blit(self.dark_overlay, (0, 0))