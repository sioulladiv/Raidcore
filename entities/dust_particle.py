
import pygame
import random


class DustParticle:
    """Floating dust particle visible in light"""

    def __init__(self, x: float, y: float, light_radius: float) -> None:
        """Spawn a dust particle near the given world position.

        Args:
            x: Initial world x-coordinate (centre of spawn area).
            y: Initial world y-coordinate (centre of spawn area).
            light_radius: Radius of the player's light cone in pixels.
        """
        self.x = x
        self.y = y
        self.light_radius = light_radius
        
        # Random position within light cone
        #put value instead of pi with math becuase i don't need to have increadible precision for this
        angle = random.uniform(0, 2 * 3.14159)
        distance = random.uniform(0, light_radius * 0.8)
        self.parralax = random.uniform(0.8, 0.9)
        self.x += distance * pygame.math.Vector2(1, 0).rotate_rad(angle).x
        self.y += distance * pygame.math.Vector2(1, 0).rotate_rad(angle).y
        
        # Very slow random drift
        self.velocity_x = random.uniform(-0.01, 0.01)
        self.velocity_y = random.uniform(-0.015, 0.005)  # Slight upward tendency
        
        self.size = random.uniform(1, 3) / 3
        self.brightness = random.randint(150, 255)
        self.alpha = random.randint(30, 80)
        
        # Floating animation
        self.time = random.uniform(0, 100)
        self.float_speed = random.uniform(0.002, 0.006)
        
    def update(self, dt: float, player_center_x: float, player_center_y: float) -> bool:
        """Update particle position with floating effect"""
        self.time += self.float_speed
        
        # Sine wave floating effect
        float_offset_x = pygame.math.Vector2(1, 0).rotate_rad(self.time).x * 0.15
        float_offset_y = pygame.math.Vector2(0, 1).rotate_rad(self.time * 0.7).y * 0.25
        
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
    
    def respawn(self, player_center_x: float, player_center_y: float, light_radius: float) -> None:
        """Reset the particle to a new random position near the player.

        Args:
            player_center_x: World x-coordinate of the player's centre.
            player_center_y: World y-coordinate of the player's centre.
            light_radius: Current radius of the light cone.
        """
        angle = random.uniform(0, 2 * 3.14159)
        distance = random.uniform(0, light_radius * 0.5)
        self.x = player_center_x + distance * pygame.math.Vector2(1, 0).rotate_rad(angle).x
        self.y = player_center_y + distance * pygame.math.Vector2(1, 0).rotate_rad(angle).y
        self.alpha = random.randint(30, 80)
        
    def draw(self, surface: pygame.Surface, camera: object) -> None:
        """Render the dust particle with alpha blending.

        Args:
            surface: Pygame surface to draw onto.
            camera: Camera object with ``zoom``, ``offset_x`` and
                ``offset_y`` attributes.
        """
        if self.alpha <= 0:
            return
        parallax = self.parralax
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
    """Manages a pool of :class:`DustParticle` objects that float within the
    player's light cone and are automatically respawned when they drift too
    far away.
    """

    def __init__(self, num_particles: int = 60, light_radius: float = 200) -> None:
        """Create a particle system.

        Args:
            num_particles: Total number of dust particles to maintain.
            light_radius: Initial radius of the light cone in pixels.
        """
        self.particles = []
        self.num_particles = num_particles
        self.light_radius = light_radius
        
    def initialize(self, player_center_x: float, player_center_y: float) -> None:
        """Spawn all particles around the player's starting position.

        Args:
            player_center_x: World x-coordinate of the player's centre.
            player_center_y: World y-coordinate of the player's centre.
        """
        self.particles = [
            DustParticle(player_center_x, player_center_y, self.light_radius)
            for _ in range(self.num_particles)
        ]
    
    def update(self, dt: float, player_center_x: float, player_center_y: float, light_radius: float) -> None:
        """Update all particles and respawn those that have drifted out of range.

        Args:
            dt: Delta time in milliseconds.
            player_center_x: World x-coordinate of the player's centre.
            player_center_y: World y-coordinate of the player's centre.
            light_radius: Current radius of the light cone.
        """
        self.light_radius = light_radius
        
        for particle in self.particles:
            should_respawn = particle.update(dt, player_center_x, player_center_y)
            if should_respawn:
                particle.respawn(player_center_x, player_center_y, light_radius)
    
    def draw(self, surface: pygame.Surface, camera: object) -> None:
        """Draw all active dust particles.

        Args:
            surface: Pygame surface to draw onto.
            camera: Camera object with ``zoom``, ``offset_x`` and
                ``offset_y`` attributes.
        """
        for particle in self.particles:
            particle.draw(surface, camera)
