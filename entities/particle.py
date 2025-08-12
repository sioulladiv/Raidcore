
import pygame
class Particle:
    def __init__(self, x, y, velocity_x, velocity_y, color, size, life_time):
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.color = color
        self.size = size
        self.max_size = size
        self.life_time = life_time
        self.max_life_time = life_time
        self.gravity = 0.1  
        self.friction = 0.98 
        
    def update(self, dt):
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        self.velocity_y += self.gravity
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        
        self.life_time -= dt / 4.0
        
        life_ratio = max(0, self.life_time / self.max_life_time)
        self.size = max(1, int(self.max_size * life_ratio)) 
        
    def draw(self, surface, camera):
        if self.life_time <= 0:
            return
            
        life_ratio = max(0, self.life_time / self.max_life_time)
        alpha = max(30, int(255 * life_ratio))  
        
        screen_x = int(self.x * camera.zoom + camera.offset_x)
        screen_y = int(self.y * camera.zoom + camera.offset_y)
        
        actual_size = max(1, int(self.size * camera.zoom))
        
        try:
            pixel_rect = pygame.Rect(screen_x - actual_size//2, 
                                    screen_y - actual_size//2, 
                                    actual_size, actual_size)
            pygame.draw.rect(surface, self.color, pixel_rect)

            if actual_size > 2:
                center_size = max(1, actual_size // 3)
                center_rect = pygame.Rect(screen_x - center_size//2, 
                                        screen_y - center_size//2, 
                                        center_size, center_size)
                pygame.draw.rect(surface, (255, 255, 255), center_rect)
        except ValueError:
            pass
    
    def is_dead(self):
        return self.life_time <= 0