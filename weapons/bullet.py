import math
import pygame
class Bullet:
    def __init__(self, x, y, angle, speed, damage, radius=4):
        self.x = x 
        self.y = y  
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.alive = True
        self.trail = []  
        self.trail_length = 3  
        self.trail_counter = 0  
        self.trail_spacing = 2  
        
        pygame.mixer.init()
        self.bullet_impact_sound = pygame.mixer.Sound("Assets/Sounds/bullet_impact.mp3")
        
    def update(self, dt=16, collision_tiles=None):  
        if self.alive:
            dx = math.cos(self.angle) * self.speed
            dy = math.sin(self.angle) * self.speed
            
            if collision_tiles:
                self.move_and_collide(dx, dy, collision_tiles)
            else:
                self.x += dx
                self.y += dy
            
            self.trail_counter += 1
            if self.trail_counter >= self.trail_spacing:
                self.trail.append((self.x, self.y))
                self.trail_counter = 0
                if len(self.trail) > self.trail_length:
                    self.trail.pop(0)
        else:
            self.trail.clear()

    def draw(self, surface, camera):
        if not self.alive and not self.trail:
            return
        
        # Draw trailing pixels (smaller white squares behind the main bullet)
        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):  # Skip the last one (current bullet position)
                trail_x, trail_y = self.trail[i]
                
                screen_x = trail_x * camera.zoom + camera.offset_x
                screen_y = trail_y * camera.zoom + camera.offset_y
                
                # Smaller pixel size for trail (gets progressively smaller)
                size_factor = (i + 1) / len(self.trail)  # 0.33, 0.66 for 3-point trail
                trail_pixel_size = max(1, int(camera.zoom * 2 * size_factor * 0.7))  # 70% of main bullet
                
                trail_rect = pygame.Rect(
                    int(screen_x - trail_pixel_size // 2),
                    int(screen_y - trail_pixel_size // 2),
                    trail_pixel_size,
                    trail_pixel_size
                )
                pygame.draw.rect(surface, (255, 255, 255), trail_rect)  # White trail pixels
        
        # Draw main bullet as a larger white pixel (square)
        if self.alive:
            screen_x = self.x * camera.zoom + camera.offset_x
            screen_y = self.y * camera.zoom + camera.offset_y
            
            # Main bullet is white and larger
            bullet_color = (255, 255, 255)  # White
            
            # Main bullet pixel size (even smaller)
            pixel_size = max(1, int(camera.zoom * 1.5))  # Even smaller square
            
            bullet_rect = pygame.Rect(
                int(screen_x - pixel_size // 2),
                int(screen_y - pixel_size // 2),
                pixel_size,
                pixel_size
            )
            pygame.draw.rect(surface, bullet_color, bullet_rect)
    
    def move_and_collide(self, dx, dy, tiles):
        new_x = self.x + dx
        bullet_rect = pygame.Rect(new_x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        
        collision = False
        for wall in tiles:
            if bullet_rect.colliderect(wall):
                collision = True
                self.bullet_impact_sound.set_volume(0.3)
                #self.bullet_impact_sound.play()
                break
        
        if not collision:
            self.x = new_x
        else:
            self.alive = False
            return
            
        new_y = self.y + dy
        bullet_rect = pygame.Rect(self.x - self.radius, new_y - self.radius, self.radius * 2, self.radius * 2)
        
        for wall in tiles:
            if bullet_rect.colliderect(wall):
                self.alive = False
                return
        
        self.y = new_y

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

    def is_completely_dead(self):
        """Check if bullet is dead (trail clears immediately)"""
        return not self.alive