import pygame


class ExperienceBar:

    def __init__(self, x, y, width, height, displaySize):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.displaySize = displaySize

        self.experience = 100

        self.border_color = (200, 200, 200)
        self.secondary_border = (241, 241, 241)
        self.background_color = (0, 0, 0)
        self.fill_color = (150, 150, 150)
        self.border_thickness = max(1, int(self.height * 0.15))

    def update(self, experience):
        self.experience = max(0, min(100, int(experience)))

    def update_animation(self, dt):
        pass

    def draw(self, screen):
        outer2 = pygame.Rect(self.x - self.border_thickness, self.y - self.border_thickness,
                             self.width + 2 * self.border_thickness, self.height + 2 * self.border_thickness)
        pygame.draw.rect(screen, self.secondary_border, outer2, self.border_thickness)

        outer1 = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, self.border_color, outer1, self.border_thickness)

        inner_x = self.x + self.border_thickness
        inner_y = self.y + self.border_thickness
        inner_w = max(0, self.width - 2 * self.border_thickness)
        inner_h = max(0, self.height - 2 * self.border_thickness)

        inner_bg = pygame.Rect(inner_x, inner_y, inner_w, inner_h)
        pygame.draw.rect(screen, self.background_color, inner_bg)

        fill_w = int(inner_w * (self.experience / 100.0))
        if fill_w > 0:
            fill_rect = pygame.Rect(inner_x, inner_y, fill_w, inner_h)
            pygame.draw.rect(screen, self.fill_color, fill_rect)
