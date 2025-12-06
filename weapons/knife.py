from weapons.item import Items
import pygame
import math
from config.game_settings import game_settings
pygame.mixer.init()


class Knife(Items): 
    def __init__(self, x, y, type, displaySize, height=40, width=5): 
        # Knife base size
        base_width, base_height = width, height
        scale_factor = 8 if type == "knife" else 1

        super().__init__(x, y, type, base_height, base_width)
        self.width = base_width * displaySize * scale_factor
        self.height = base_height * displaySize * scale_factor
        self.displaySize = displaySize
        self.type = type
        self.attack_speed = 0.3
        self.attack_timer = 0
        self.damage = 2
        self.angle = 0
        self.y_offset = 6 * self.displaySize
        self.orbit_distance = 5 * self.displaySize
        self.angle_offset = 0
        self.can_attack = True
        
        # Slash animation properties
        self.is_slashing = False
        self.slash_rotation = 0  # Current rotation offset during slash
        self.slash_progress = 0  # 0 to 1 progress of slash animation
        self.slash_particles = []

        try:
            self.slash_sound = pygame.mixer.Sound("Assets/Sounds/gunshot.mp3")  # Replace with knife slash sound
            self.slash_sound.set_volume(0.4)
        except pygame.error:
            print("Warning: Could not load slash sound file")
            self.slash_sound = None

        if self.type == "knife":
            self.attack_speed = 0.2  # Faster animation (was 0.3)
            self.damage = 2
            self.image = pygame.image.load("./Dungeon/frames/knife.png")  # Replace with knife.png
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
    
    def update(self, camera=None, player=None, dt=0, collision_tiles=None):
        if not hasattr(self, 'pointing_left'):
            self.pointing_left = False
        
        if self.attack_timer > 0:
            self.attack_timer -= dt / 1000.0 
            self.can_attack = False
            
            # Update slash animation
            self.slash_progress = 1 - (self.attack_timer / self.attack_speed)
            # Rotate 120 degrees during slash (smooth ease-out)
            rotation_amount = math.radians(120) * math.sin(self.slash_progress * math.pi / 2)
            # Reverse rotation direction when facing left
            self.slash_rotation = -rotation_amount if self.pointing_left else rotation_amount
        else:
            self.can_attack = True
            self.slash_rotation = 0
            self.slash_progress = 0
        
        # Update slash particles
        for particle in list(self.slash_particles):
            particle['life'] -= dt / 1000.0
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vx'] *= 0.95
            particle['vy'] *= 0.95
            if particle['life'] <= 0:
                self.slash_particles.remove(particle)
            
        if camera and player:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            player_center_x = player.x + player.width / 2
            player_center_y = player.y + player.height / 2 + self.y_offset
            world_mouse_x = (mouse_x - camera.offset_x) / camera.zoom
            world_mouse_y = (mouse_y - camera.offset_y) / camera.zoom
            base_angle = math.atan2(world_mouse_y - player_center_y, world_mouse_x - player_center_x)
            
            if self.pointing_left and (base_angle < math.pi/2 - 0.1 and base_angle > -math.pi/2 + 0.1):
                self.pointing_left = False
            elif not self.pointing_left and (base_angle > math.pi/2 + 0.1 or base_angle < -math.pi/2 - 0.1):
                self.pointing_left = True
            if self.pointing_left:
                self.angle = base_angle - self.angle_offset
            else:
                self.angle = base_angle + self.angle_offset
        
        elif player:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            player_center_x = player.x + player.width / 2
            player_center_y = player.y + player.height / 2 + self.y_offset
            
            self.angle = math.atan2(mouse_y - player_center_y, mouse_x - player_center_x)
        else:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.angle = math.atan2(mouse_y - self.y, mouse_x - self.x)

    def draw(self, surface, camera=None, player=None, dt=0):
        if player: 
            pivot_x = player.x + player.width / 2
            pivot_y = player.y + player.height / 2 + self.y_offset
            
            self.x = pivot_x + math.cos(self.angle) * self.orbit_distance
            self.y = pivot_y + math.sin(self.angle) * self.orbit_distance
        
        # Draw slash particles
        if camera:
            for particle in self.slash_particles:
                screen_x = particle['x'] * camera.zoom + camera.offset_x
                screen_y = particle['y'] * camera.zoom + camera.offset_y
                alpha = int(255 * (particle['life'] / 0.2))
                size = max(1, int(particle['size'] * camera.zoom * (particle['life'] / 0.2)))
                
                # Draw white slash particle
                if alpha > 0:
                    pygame.draw.circle(surface, (255, 255, 255), (int(screen_x), int(screen_y)), size)
        
        knife_image = self.image
        
        if self.pointing_left:
            knife_image = pygame.transform.flip(knife_image, False, True)
        
        # Apply slash rotation during attack
        total_rotation = self.angle + self.slash_rotation
        rotated_image = pygame.transform.rotate(knife_image, -math.degrees(total_rotation))
        rotated_rect = rotated_image.get_rect()
        
        if camera:
            draw_x = self.x * camera.zoom + camera.offset_x
            draw_y = self.y * camera.zoom + camera.offset_y
            
            rotated_rect.center = (draw_x, draw_y)
            
            surface.blit(rotated_image, rotated_rect)
        else:
            rotated_rect.center = (self.x, self.y)
            
            surface.blit(rotated_image, rotated_rect)
        
        # Handle knife attack on mouse click
        if pygame.mouse.get_pressed()[0] and player and camera and self.can_attack:
            self.attack_timer = self.attack_speed
            self.is_slashing = True

            if self.slash_sound:
                base_volume = 0.3
                final_volume = base_volume * game_settings.get_sfx_volume()
                self.slash_sound.set_volume(final_volume)
                self.slash_sound.play()
            
            # Create slash effect particles (smaller)
            import random
            for i in range(3):  # Fewer particles (was 5)
                angle_offset = random.uniform(-0.2, 0.2)
                particle_angle = self.angle + angle_offset
                distance = random.uniform(8, 15)  # Shorter distance
                particle_x = self.x + math.cos(particle_angle) * distance
                particle_y = self.y + math.sin(particle_angle) * distance
                
                self.slash_particles.append({
                    'x': particle_x,
                    'y': particle_y,
                    'vx': math.cos(particle_angle) * random.uniform(0.3, 0.8),  # Slower velocity
                    'vy': math.sin(particle_angle) * random.uniform(0.3, 0.8),
                    'size': random.uniform(1, 2),  # Smaller size (was 2-4)
                    'life': 0.15  # Shorter life (was 0.2)
                })

    def get_attack_rect(self, camera=None):
        """Returns the attack hitbox rectangle for the knife"""
        if not hasattr(self, 'x') or not hasattr(self, 'y'):
            return None
            
        # Create attack range in front of knife
        attack_range = 10
        attack_width = 20
        attack_height = 20
        
        attack_x = self.x + math.cos(self.angle) * attack_range
        attack_y = self.y + math.sin(self.angle) * attack_range
        
        return pygame.Rect(
            attack_x - attack_width // 2,
            attack_y - attack_height // 2,
            attack_width,
            attack_height
        )
