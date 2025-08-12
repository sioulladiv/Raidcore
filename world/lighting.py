import pygame
class Lighting:
    def __init__(self, radius, darkness=210):
        self.radius = radius
        self.darkness = darkness

        self.surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        for r in range(radius):
            alpha = int((r / radius) * self.darkness)
            pygame.draw.circle(self.surface, (0, 255, 0, alpha), (radius, radius), radius - r)

    def update(self, player, camera, darkness=210):
        self.darkness = darkness

        player_center_x = player.x + (player.width / 2)
        player_center_y = player.y + (player.height / 2)
        
        self.x = player_center_x * camera.zoom + camera.offset_x
        self.y = player_center_y * camera.zoom + camera.offset_y
        
    def draw(self, surface, camera):
        dark_overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, self.darkness))
        
        center_x = self.x
        center_y = self.y
        
        dark_overlay.blit(self.surface, (center_x - self.radius, center_y - self.radius), special_flags=pygame.BLEND_RGBA_SUB)
        
        surface.blit(dark_overlay, (0, 0))