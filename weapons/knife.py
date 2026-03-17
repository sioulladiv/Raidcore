from __future__ import annotations

from weapons.item import Items
import pygame
import math
from typing import TYPE_CHECKING
from config.game_settings import game_settings

if TYPE_CHECKING:
    from world.camera import Camera
    from entities.player import Player

pygame.mixer.init()


class Knife(Items):
    """Melee knife weapon that swings in an arc on left-click.

    Emits a short slash animation and exposes a
    hit-box rectangle queried by enemies to detect damage each frame.
    """
    def __init__(self, x: float, y: float, type: str, displaySize: float, height: int = 40, width: int = 5) -> None:
        """Create a Knife and load its sprite and sound assets.

        Args:
            x: Initial world x-coordinate.
            y: Initial world y-coordinate.
            type: Weapon type identifier (currently only ``'knife'``
                is supported).
            displaySize: Scaling ratio (screen_width / 2560).
            height: Base sprite height before scaling (default 40).
            width: Base sprite width before scaling (default 5).
        """
        # Knife base size
        base_width, base_height = width, height
        scale_factor = 8 if type == "knife" else 1

        super().__init__(x, y, type, base_height, base_width)
        self.width = base_width*displaySize*scale_factor
        self.height = base_height *displaySize*scale_factor
        self.displaySize = displaySize
        self.type = type

        self.attackspeed = 0.3
        self.attacktimer = 0
        self.damage = 0.5


        self.angle = 0

        self.y_offset =6*self.displaySize
        self.orbital_distance = 5*self.displaySize

        self.angleOffset = 0
        self.can_attack = True
        self.pointing_left = False  
        
        # Slash animation properties
        self.is_slashing = False
        self.slash_rotation = 0  # Current rotation offset during slash
        self.slash_progress = 0  #0 to 1 progress of slash animation

        try:
            self.slash_sound = pygame.mixer.Sound("Assets/Sounds/sword.mp3")  
            
            self.slash_sound.set_volume(0.4)
        except pygame.error:
            print("Can't load slash sound file")

            self.slash_sound = None

        if self.type == "knife":
            self.attackspeed = 0.2  
            self.damage = 2
            self.image = pygame.image.load("./Dungeon/frames/knife.png")  
            self.image = pygame.transform.scale(self.image,(self.width, self.height))
    
    def update(self, camera: Camera | None = None,player:Player|None =None, dt: float = 0, collision_tiles: list[pygame.Rect] | None = None) -> None:
        """
        Update knife angle and slash animation.

        Args:
            camera: Active camera for world to mouse coordinate conversion.
            player: Player entity used to anchor the knife's orbit position.
            dt: Delta time in milliseconds.
            collision_tiles: Unused; kept for signature parity with Gun.
        """
        if not hasattr(self, 'pointing_left'):
            self.pointing_left = False
        
        if self.attacktimer > 0:

            self.attacktimer -= dt/1000.0 
            self.can_attack = False
            
            #update slash animation
            self.slash_progress = 1 - (self.attacktimer / self.attackspeed)
            # rotate 120 degrees during slash (smootly using sine)
            #looks smoother than just linear interpolation
            rotation_amount = math.radians(120) * math.sin(self.slash_progress * math.pi / 2)

            #reverse rotation direction when facing left
            self.slash_rotation = -rotation_amount if self.pointing_left else rotation_amount
        else:
            # reset slash if not attacking
            self.can_attack = True
            self.slash_rotation = 0

            self.slash_progress = 0
            
        if camera and player:
            mouse_x,mouse_y = pygame.mouse.get_pos()

            player_center_x = player.x + player.width/2
            player_center_y = player.y + player.height/2 +self.y_offset

            world_mouse_x = (mouse_x - camera.offset_x)/camera.zoom
            world_mouse_y = (mouse_y -camera.offset_y)/ camera.zoom
            # Get angle from player to mouse
            baseAngle = math.atan2( world_mouse_y - player_center_y, world_mouse_x - player_center_x)
            # Flip knife based on angle to prevent upside down sprite which looks off
            if self.pointing_left and (baseAngle <math.pi/2 - 0.1 and baseAngle >-math.pi /2 +0.1):
                self.pointing_left = False
            # There is a small deadzone in the middle of the animation so that you don't get jitter when crossing vertical axis
            elif not self.pointing_left and (baseAngle > math.pi/2 + 0.1 or baseAngle<-math.pi/2 - 0.1):
                self.pointing_left = True
            
            # adjust angle to flip sprute when pointing left so that it always swing in the same direction
            if self.pointing_left:
                self.angle = baseAngle- self.angleOffset
            else:
                self.angle = baseAngle+ self.angleOffset
        
        elif player:
            # debug mode so that if no camera just point toward mouse without converting world coords
            mouse_x, mouse_y = pygame.mouse.get_pos()

            player_center_x = player.x + player.width/2
            player_center_y = player.y + player.height/2 +self.y_offset
            
            self.angle = math.atan2(mouse_y - player_center_y, mouse_x - player_center_x)
        else:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.angle = math.atan2(mouse_y - self.y, mouse_x - self.x)

    def draw(self, surface: pygame.Surface, camera: Camera|None = None, player: Player|None = None, dt: float = 0) -> None:
        """
        Render the knife sprite and trigger an attack swing on click.

        Args:
            surface: Pygame surface to draw onto.
            camera: Active camera for coordinate transformations.
            player: Player entity used to anchor the knife.
            dt: Delta time in milliseconds.
        """

        # Position the knife in orbit around character with a y_offset to make it natural
        #so that it doesn't orbit around feet
        if player:
            pivot_x = player.x + player.width/2

            pivot_y = player.y + player.height/2+ self.y_offset

            self.x = pivot_x + math.cos(self.angle)*self.orbital_distance
            self.y = pivot_y + math.sin(self.angle)*self.orbital_distance

        knife_image= self.image

        # Flip knige sprite if pointing left to prevent upide down sprite which looks weird
        if self.pointing_left: knife_image = pygame.transform.flip(knife_image, False, True)

        total_rotation=self.angle +self.slash_rotation
        
        rotated_image = pygame.transform.rotate(knife_image, -math.degrees(total_rotation))
        rotated_rect = rotated_image.get_rect()

        # If camera is available convert world coordinates to screen coordinates for drawing
        if camera:
            draw_x = self.x * camera.zoom + camera.offset_x
            draw_y = self.y * camera.zoom + camera.offset_y

            rotated_rect.center = (draw_x, draw_y)

            surface.blit(rotated_image, rotated_rect)
        else:
            #if no camera just draw at world coords (debug)
            rotated_rect.center = (self.x, self.y)

            surface.blit(rotated_image, rotated_rect)
        
        # Handle knife attack on mouse click
        if pygame.mouse.get_pressed()[0] and player and camera and self.can_attack:
            self.attacktimer = self.attackspeed
            self.is_slashing = True
            # play slash sound with settings volume applied
            if self.slash_sound:
                base_volume = 0.3
                final_volume = base_volume * game_settings.get_sfx_volume()
                self.slash_sound.set_volume(final_volume)
                self.slash_sound.play()

    def get_attack_rect(self, camera: Camera| None = None) -> pygame.Rect | None:
        """Returns the attack hitbox rectangle for the knife"""

        if not hasattr(self, 'x') or not hasattr(self, 'y'):
            return None
        
        
        # Calculate center of the attack hitbox based on the knife angle and range
        attack_x = self.x + math.cos(self.angle)*10
        attack_y = self.y + math.sin(self.angle)*10
        
        return pygame.Rect(

            attack_x - 10,
            attack_y - 10,
            20,
            20
        )
