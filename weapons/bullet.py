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
        self.trail_length = 5
        self.death_position = None
        self.trail_dying = False
        self.trail_move_timer = 0
        self.trail_move_speed = 50 
        
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 50  
        
        self.trail.append((self.x, self.y))
        self.animation = []
        for i in range(20):
            img = pygame.image.load(f"./Dungeon/frames/bullet{'0' + str(i) if i < 10 else str(i)}.png")
            img = pygame.transform.scale(img, (radius * 4, radius * 4))  
            self.animation.append(img)
        
    def update(self, dt=16, collision_tiles=None):  
        if self.alive:
            dx = math.cos(self.angle) * self.speed
            dy = math.sin(self.angle) * self.speed
            
            if collision_tiles:
                self.move_and_collide(dx, dy, collision_tiles)
            else:
                self.x += dx
                self.y += dy
            
            self.trail.append((self.x, self.y))
            if len(self.trail) > self.trail_length:
                self.trail.pop(0)
        else:
            if not self.trail_dying:
                self.death_position = (self.x, self.y)
                self.trail_dying = True
            
            self.trail_move_timer += dt
            if self.trail_move_timer >= self.trail_move_speed and self.trail:
                self.trail_move_timer = 0
                
                new_trail = []
                for i, (trail_x, trail_y) in enumerate(self.trail):
                    if i < len(self.trail) - 1:
                        next_x, next_y = self.trail[i + 1]
                    else:
                        next_x, next_y = self.death_position
                    
                    dx = next_x - trail_x
                    dy = next_y - trail_y
                    distance = math.sqrt(dx * dx + dy * dy)
                    
                    if distance > self.speed / 2: 
                        dx = (dx / distance) * self.speed
                        dy = (dy / distance) * self.speed
                        new_trail.append((trail_x + dx, trail_y + dy))
                    elif distance > 1:  
                        new_trail.append((next_x, next_y))
                
                self.trail = new_trail
            
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.animation)
            self.animation_timer = 0

    def draw(self, surface, camera):
        if not self.trail:
            return
            
        for i, (trail_x, trail_y) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            
            screen_x = trail_x * camera.zoom + camera.offset_x
            screen_y = trail_y * camera.zoom + camera.offset_y
            
            size = max(1, int(self.radius * (i / len(self.trail)) * camera.zoom))
            
            pygame.draw.circle(surface, (255, i * 50, 0), (int(screen_x), int(screen_y)), size)
        
        if self.alive:
            screen_x = self.x * camera.zoom + camera.offset_x
            screen_y = self.y * camera.zoom + camera.offset_y
            
            current_image = self.animation[self.current_frame]
            
            rotated_image = pygame.transform.rotate(current_image, -math.degrees(self.angle))
            
            if camera.zoom != 1.0:
                scaled_width = int(rotated_image.get_width() * camera.zoom)
                scaled_height = int(rotated_image.get_height() * camera.zoom)
                rotated_image = pygame.transform.scale(rotated_image, (scaled_width, scaled_height))
            
            image_rect = rotated_image.get_rect()
            image_rect.center = (int(screen_x), int(screen_y))
            
            surface.blit(rotated_image, image_rect)
    
    def move_and_collide(self, dx, dy, tiles):
        new_x = self.x + dx
        bullet_rect = pygame.Rect(new_x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        
        collision = False
        for wall in tiles:
            if bullet_rect.colliderect(wall):
                collision = True
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
        """Check if bullet and all trail points are dead"""
        return not self.alive and len(self.trail) == 0