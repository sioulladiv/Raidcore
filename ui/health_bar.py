import pygame


class HealthBar:

    def __init__(self, x, y, width, height, displaySize):
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
        self.border_thickness = max(1, int(self.height * 0.07))

    def update(self, life):
        self.life = max(0, min(100, int(life)))

    def damage(self, damage_amount):
        self.update(self.life - damage_amount)

    def update_animation(self, dt):
        pass

    def draw(self, screen, player, camera):
        zoom = camera.zoom
        
        # Calculate scaled dimensions
        scaled_width = self.width * zoom
        scaled_height = self.height * zoom
        scaled_border = max(1, int(self.border_thickness * zoom))
        
        # Position health bar centered above player's head
        self.x = (player.x + player.width / 2) * zoom + camera.offset_x - scaled_width / 2
        self.y = (player.y - 15) * zoom + camera.offset_y +180
        
        outer1 = pygame.Rect(self.x, self.y, scaled_width, scaled_height)
        pygame.draw.rect(screen, self.border_color, outer1, scaled_border)

        inner_x = self.x + scaled_border
        inner_y = self.y + scaled_border
        inner_w = max(0, scaled_width - 2 * scaled_border)
        inner_h = max(0, scaled_height - 2 * scaled_border)

        inner_bg = pygame.Rect(inner_x, inner_y, inner_w, inner_h)
        pygame.draw.rect(screen, self.background_color, inner_bg)

        fill_w = int(inner_w * (self.life / 100.0))
        if fill_w > 0:
            fill_rect = pygame.Rect(inner_x, inner_y, fill_w, inner_h)
            pygame.draw.rect(screen, self.fill_color, fill_rect)
