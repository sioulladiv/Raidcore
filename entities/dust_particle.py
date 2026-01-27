import pygame
import random

class DustParticle:
    """Floating dust particle visible in light"""
    def __init__(self, x, y, light_radius):
        self.x = x
        self.y = y
        self.light_radius = light_radius
        
        # Random position within light cone
        angle = random.uniform(0, 2 * 3.14159)
        distance = random.uniform(0, light_radius * 0.8)
        self.x += distance * pygame.math.Vector2(1, 0).rotate_rad(angle).x
        self.y += distance * pygame.math.Vector2(1, 0).rotate_rad(angle).y
        
        # Very slow random drift
        self.velocity_x = random.uniform(-0.2, 0.2)
        self.velocity_y = random.uniform(-0.3, 0.1)  # Slight upward tendency
        
        self.size = random.uniform(1, 4) /2
        self.brightness = random.randint(150, 255)
        self.alpha = random.randint(30, 80)
        
        # Floating animation
        self.time = random.uniform(0, 100)
        self.float_speed = random.uniform(0.02, 0.05)
        
    def update(self, dt, player_center_x, player_center_y):
        """Update particle position with floating effect"""
        self.time += self.float_speed
        
        # Sine wave floating effect
        float_offset_x = pygame.math.Vector2(1, 0).rotate_rad(self.time).x * 0.3
        float_offset_y = pygame.math.Vector2(0, 1).rotate_rad(self.time * 0.7).y * 0.5
        
        self.x += self.velocity_x + float_offset_x
        self.y += self.velocity_y + float_offset_y
        
        # Calculate distance from player (light source)
        dx = self.x - player_center_x
        dy = self.y - player_center_y
        distance = (dx**2 + dy**2)**0.5
        
        # Fade out as particle moves away from light
        if distance > self.light_radius * 0.6:
            self.alpha = max(0, self.alpha - 2)
        
        # Respawn near player if too far
        return distance > self.light_radius
    
    def respawn(self, player_center_x, player_center_y, light_radius):
        """Respawn particle near player"""
        angle = random.uniform(0, 2 * 3.14159)
        distance = random.uniform(0, light_radius * 0.5)
        self.x = player_center_x + distance * pygame.math.Vector2(1, 0).rotate_rad(angle).x
        self.y = player_center_y + distance * pygame.math.Vector2(1, 0).rotate_rad(angle).y
        self.alpha = random.randint(30, 80)
        
    def draw(self, surface, camera):
        """Draw dust particle"""
        if self.alpha <= 0:
            return
            
        screen_x = int(self.x * camera.zoom + camera.offset_x)
        screen_y = int(self.y * camera.zoom + camera.offset_y)
        
        actual_size = max(1, int(self.size * camera.zoom))
        
        # Draw with warm color and transparency
        color = (self.brightness, int(self.brightness * 0.85), int(self.brightness * 0.6), self.alpha)
        
        try:
            # Create small surface for particle with alpha
            particle_surface = pygame.Surface((actual_size * 2, actual_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (actual_size, actual_size), actual_size)
            surface.blit(particle_surface, (screen_x - actual_size, screen_y - actual_size))
        except (ValueError, pygame.error):
            pass


class DustParticleSystem:
    """Manages multiple dust particles in the light"""
    def __init__(self, num_particles=60, light_radius=200):
        self.particles = []
        self.num_particles = num_particles
        self.light_radius = light_radius
        
    def initialize(self, player_center_x, player_center_y):
        """Create initial particles"""
        self.particles = [
            DustParticle(player_center_x, player_center_y, self.light_radius)
            for _ in range(self.num_particles)
        ]
    
    def update(self, dt, player_center_x, player_center_y, light_radius):
        """Update all particles"""
        self.light_radius = light_radius
        
        for particle in self.particles:
            should_respawn = particle.update(dt, player_center_x, player_center_y)
            if should_respawn:
                particle.respawn(player_center_x, player_center_y, light_radius)
    
    def draw(self, surface, camera):
        """Draw all particles"""
        for particle in self.particles:
            particle.draw(surface, camera)
