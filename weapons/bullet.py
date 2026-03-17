"""Bullet projectile for the gun weapon."""
from __future__ import annotations

import math
import pygame

from world.camera import Camera


class Bullet:
    """A projectile fired by the :class: `~weapons.gun.Gun`.

    Travels in a straight line, leaves a short pixel trail, and is destroyed
    on contact with a wall tile.
    """

    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        speed: float,
        damage: float,
        radius: float = 4,
    ) -> None:
        """Create a bullet.

        Args:
            x: Spawn world x-coordinate.
            y: Spawn world y-coordinate.
            angle: Travel direction in radians.
            speed: Pixels moved per frame
            damage: Hit-points removed from the target on impact
            radius: Collision radius in pixels 
        """

        self.x = x 
        self.y = y  
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.alive = True
        self.trail = []  
        self.trail_length = 3  
        self.trailCounter = 0  
        self.trailSpacing = 2  
        
        pygame.mixer.init()

        self.bullet_impact_sound = pygame.mixer.Sound("Assets/Sounds/bullet_impact.mp3")
        
    def update(self, dt: float = 16.67, collision_tiles: list[pygame.Rect]|None=None)-> None:

        """
        Advance the bullet position and update its trail.

        Args:
            dt: Delta time in milliseconds.
            collision_tiles: Wall rectangles to test for impact; when
            ``None`` no collision is checked.

        """
        if self.alive:
            # Calculate delta time factor for 60 FPS 
            dt_factor = dt / 16.67  # 16.67ms = 1 frame at 60 FPS
            
            # Move bullet
            dx = math.cos(self.angle) * self.speed * dt_factor
            dy = math.sin(self.angle) * self.speed * dt_factor
            
            # Check for collisions with walls
            if collision_tiles:
                self.move_and_collide(dx, dy, collision_tiles)
            else:
                self.x += dx
                self.y += dy
            
            # Update trail
            self.trailCounter += 1
            if self.trailCounter >= self.trailSpacing:

                self.trail.append((self.x, self.y))
                self.trailCounter = 0
                if len( self.trail) > self.trail_length:
                    self.trail.pop(0)
        else:
            self.trail.clear()

    def draw(self, surface: pygame.Surface, camera: Camera)-> None:

        """Render the bullet and its trail.

        Args:
            surface: Pygame surface to draw onto.
            camera: Camera for world toscreen transformation.

        """

        # Don't draw if bullet is dead and trail empty
        if not self.alive and not self.trail:

            return
        
        # Draw trailing pixels (just smaller white squares behind the main bullet)
        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):  # Skip the last one which is current bullet position
                trail_x, trail_y = self.trail[i]
                
                # Transform to screen coordinates
                screen_x = trail_x * camera.zoom + camera.offset_x
                screen_y = trail_y * camera.zoom + camera.offset_y
                
                # Smaller pixel size for trail (gets progressively smaller)
                size_factor = (i + 1) / len(self.trail)  # 0.33, 0.66 for 3-point trail
                trail_pixel_size = max(1, int(camera.zoom * 2 * size_factor * 0.7))  # 70% of main bullet
                
                # Draw white square for trail pixel
                trail_rect = pygame.Rect(

                    int(screen_x - trail_pixel_size // 2),
                    int(screen_y - trail_pixel_size // 2),
                    trail_pixel_size,
                    trail_pixel_size

                )
                pygame.draw.rect(surface, (255, 255, 255), trail_rect)  
                # White trail pixels
        
        # Draw main bullet as a larger white squaere
        if self.alive:
            screen_x = self.x * camera.zoom + camera.offset_x
            screen_y = self.y * camera.zoom + camera.offset_y
            
            # Main bullet is white and larger
            bullet_color = (255, 255, 255)  
            
            # Main bullet pixel size
            pixel_size = max(1, int(camera.zoom * 1.5))
            
        
            bullet_rect = pygame.Rect( int(screen_x - pixel_size // 2), int(screen_y - pixel_size // 2), pixel_size, pixel_size
            )
            pygame.draw.rect(surface, bullet_color, bullet_rect)
    
    def move_and_collide(self, dx: float, dy: float, tiles: list[pygame.Rect]) -> None:
        """Move the bullet along each axis and mark it dead on wall impact.

        Args:
            dx: Horizontal movement this frame.
            dy: Vertical movement this frame.
            tiles: Wall collision rectangles.
        """

        # Move horizontally and check for collisions
        new_x = self.x + dx

        bullet_rect = pygame.Rect(new_x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        
        # chheck for collision with any wall tiles
        collision = False
        for wall in tiles:
            if bullet_rect.colliderect(wall):
                collision = True
                self.bullet_impact_sound.set_volume(0.3)
                #self.bullet_impact_sound.play()
                break
        
        # If no collision, update position else  mark bullet as dead
        if not collision: self.x= new_x
        else:
            self.alive = False
            return
            
        new_y=self.y +dy

        
        bullet_rect = pygame.Rect(self.x -self.radius  ,new_y-self.radius , self.radius*2, self.radius * 2)
        
        
        for wall in tiles:
            if bullet_rect.colliderect(wall):
                self.alive = False
                return
        
        self.y = new_y

    def get_rect(self) -> pygame.Rect:
        """
        Return a rectangle used for hit-testing.

        Returns:
            ``pygame.Rect`` centred on the bullet with sides 2*radius.
        """

        return pygame.Rect(self.x - self.radius,self.y - self.radius, self.radius * 2,self.radius * 2)

    def is_completely_dead(self) -> bool:
        #true if bullet is dead and trail empy
        return not self.alive