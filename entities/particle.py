import pygame


class Particle:
    """A single short-lived particle used for visual effects.

    Each particle has a position, velocity, colour and lifetime.  It applies
    simple gravity and friction on every update and fades/shrinks as it ages.
    """

    def __init__(self,x: float,y: float,velocity_x: float,velocity_y: float,color: tuple[int, int, int],size: int,life_time: float,) -> None:
        """Create a particle.

        Args:
            x: Initial world x-coordinate.
            y: Initial world y-coordinate.
            velocity_x: Horizontal velocity in pixels per frame.
            velocity_y: Vertical velocity in pixels per frame.
            color: RGB colour tuple.
            size: Initial radius in pixels.
            life_time: How many frames the particle lives before dying.
        """
        self.x = x
        self.y = y

        self.velocity_x = velocity_x
        self.velocity_y = velocity_y

        self.color = color
        self.size = size
        self.max_size = size


        # Lifetime is measured in frames the particle dies when it reaches 0
        self.life_time = life_time
        self.max_life_time = life_time
        self.gravity = 0.1  
        self.friction = 0.98 
        
    def update(self, dt: float) -> None:
        """Advance physics and age the particle by one tick.

        Args:
            dt: Delta time in milliseconds (used to normalise lifetime decay).
        """
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Apply gravity and friction
        self.velocity_y += self.gravity
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        
        self.life_time -= dt / 4.0
        # Update size based on remaining lifetime
        life_ratio = max(0, self.life_time / self.max_life_time)
        self.size = max(1, int(self.max_size * life_ratio)) 
        
    def draw(self, surface: pygame.Surface, camera: object) -> None:
        """Render the particle to *surface* using *camera* for world→screen
        coordinate transformation.

        Args:
            surface: Pygame surface to draw onto.
            camera: Camera object providing ``zoom``, ``offset_x`` and
                ``offset_y`` attributes.
        """
        if self.life_time <= 0:
            return
            
        life_ratio = max(0, self.life_time / self.max_life_time)
        alpha = max(30, int(255 * life_ratio))  
        # Apply alpha to color
        screen_x = int(self.x *camera.zoom+camera.offset_x)
        screen_y = int(self.y* camera.zoom+camera.offset_y)
        
        actual_size = max(1,int(self.size*camera.zoom))
        # draw with alpha
        try:
            pixel_rect = pygame.Rect(screen_x - actual_size//2, screen_y - actual_size//2, actual_size, actual_size)
            pygame.draw.rect(surface, self.color, pixel_rect)

            # Add a bright center for larger particles to make it prettier
            if actual_size > 2:
                centre_size = max(1, actual_size // 3)
                center_rect = pygame.Rect(screen_x -centre_size //2, screen_y -centre_size //2, centre_size, centre_size)
                pygame.draw.rect(surface, (255, 255, 255), center_rect)

        #if error ignore so no crashing        
        except ValueError:
            pass

    # Return True when the particle's lifetime has expired and it should be removed
    def is_dead(self) -> bool:
        """Return ``True`` when the particle's lifetime has expired."""
        return self.life_time <= 0