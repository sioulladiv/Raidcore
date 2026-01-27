from weapons.item import Items
import pygame
import math
from weapons.bullet import Bullet
from utils.culling import FrustumCuller
import random
from config.game_settings import game_settings
pygame.mixer.init()



class Gun(Items): 
    def __init__(self, x, y, type, displaySize, height=9, width=10): 
        # Use per-weapon base size; pistol is small (10x6) and gets a scale boost
        base_width, base_height = width, height
        scale_factor = 10 if type == "pistol" else 1

        super().__init__(x, y, type, base_height, base_width)
        self.width = base_width * displaySize * scale_factor
        self.height = base_height * displaySize * scale_factor
        self.displaySize = displaySize
        self.type = type
        self.ammo = 0
        self.max_ammo = 100
        self.shoot_speed = 1.5
        self.shoot_timer = 0
        self.bullet_speed = 10
        self.bullet_damage = 1
        self.bullet_radius = 5 * self.displaySize
        self.angle = 0
        self.y_offset = 6 * self.displaySize
        self.orbit_distance = 5 * self.displaySize
        self.angle_offset = 0

        self.bullets = []
        self.can_shoot = True

        self.fps_text_font = pygame.font.SysFont("Verdana", 50)
        self.ammo_image = pygame.image.load("./Dungeon/frames/ammo.png")


        try:
            self.gunshot_sound = pygame.mixer.Sound("Assets/Sounds/gunshot.mp3")
            self.gunshot_sound.set_volume(0.4)
        except pygame.error:
            print("Warning: Could not load gunshot sound file")
            self.gunshot_sound = None

        if self.type == "pistol":
            self.ammo = self.max_ammo
            self.max_ammo = 10
            self.shoot_speed = 0.5
            self.bullet_speed = 5  
            self.bullet_damage = 1 
            self.bullet_radius = max(0.5, self.displaySize * 0.8)  # Smaller radius for better collision
            self.image = pygame.image.load("./Dungeon/frames/pistol.png")
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
    
    def update(self, camera=None, player=None, dt=0, collision_tiles=None):
        if not hasattr(self, 'pointing_left'):
            self.pointing_left = False
        
        if self.shoot_timer > 0:
            self.shoot_timer -= dt / 1000.0 
            self.can_shoot = False
        else:
            self.can_shoot = True
            
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
                self.angle = base_angle  - self.angle_offset
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

        # Optimize bullet update with list comprehension
        if camera:
            margin = 300
            screen_width = pygame.display.get_surface().get_width()
            screen_height = pygame.display.get_surface().get_height()
            
            min_x = (0 - camera.offset_x) / camera.zoom - margin
            min_y = (0 - camera.offset_y) / camera.zoom - margin
            max_x = (screen_width - camera.offset_x) / camera.zoom + margin
            max_y = (screen_height - camera.offset_y) / camera.zoom + margin
            
            # Update and filter bullets in one pass
            updated_bullets = []
            for bullet in self.bullets:
                bullet.update(dt, collision_tiles)
                if not bullet.is_completely_dead():
                    if (bullet.x >= min_x and bullet.x <= max_x and 
                        bullet.y >= min_y and bullet.y <= max_y):
                        updated_bullets.append(bullet)
            self.bullets = updated_bullets
        else:
            self.bullets = [b for b in self.bullets if (b.update(dt, collision_tiles), not b.is_completely_dead())[1]]

    def draw(self, surface, camera=None, player=None, dt=0):
        if player: 
            pivot_x = player.x + player.width / 2
            pivot_y = player.y + player.height / 2 + self.y_offset
            
            self.x = pivot_x + math.cos(self.angle) * self.orbit_distance
            self.y = pivot_y + math.sin(self.angle) * self.orbit_distance
        
        gun_image = self.image
        
        if self.pointing_left:
            gun_image = pygame.transform.flip(gun_image, False, True)
        
        rotated_image = pygame.transform.rotate(gun_image, -math.degrees(self.angle))
        rotated_rect = rotated_image.get_rect()
        
        if camera:
            draw_x = self.x * camera.zoom + camera.offset_x
            draw_y = self.y * camera.zoom + camera.offset_y
            
            rotated_rect.center = (draw_x, draw_y)
            
            surface.blit(rotated_image, rotated_rect)
        else:
            rotated_rect.center = (self.x, self.y)
            
            surface.blit(rotated_image, rotated_rect)
        
        if pygame.mouse.get_pressed()[0] and player and camera and self.can_shoot:
            if self.ammo > 0:
                self.shoot_timer = self.shoot_speed

                if self.gunshot_sound:
                    base_volume = random.uniform(0.2, 0.5)
                    final_volume = base_volume * game_settings.get_sfx_volume()
                    self.gunshot_sound.set_volume(final_volume)
                    self.gunshot_sound.play()

                mouse_x, mouse_y = pygame.mouse.get_pos()
                world_mouse_x = (mouse_x - camera.offset_x) / camera.zoom
                world_mouse_y = (mouse_y - camera.offset_y) / camera.zoom

                if self.pointing_left:
                    self.bullet_angle = self.angle + self.angle_offset
                else:
                    self.bullet_angle = self.angle - 2.2*self.angle_offset
                barrel_length = 10
                barrel_x = self.x + math.cos(self.bullet_angle) * (barrel_length-6)
                barrel_y = self.y + math.sin(self.bullet_angle) * (barrel_length-6)

                bullet_angle = math.atan2(world_mouse_y - barrel_y, world_mouse_x - barrel_x)
                bullet = Bullet(
                    barrel_x,
                    barrel_y,
                    self.angle,
                    self.bullet_speed,
                    self.bullet_damage,
                    self.bullet_radius
                )
                self.bullets.append(bullet)
                self.ammo -=1
            else:
                print("no bullets")
        
        for bullet in self.bullets:
            if camera:
                screen_x = bullet.x * camera.zoom + camera.offset_x
                screen_y = bullet.y * camera.zoom + camera.offset_y
                
                margin = 100
                screen_width = pygame.display.get_surface().get_width()
                screen_height = pygame.display.get_surface().get_height()
                
                if (screen_x >= -margin and screen_x <= screen_width + margin and
                    screen_y >= -margin and screen_y <= screen_height + margin):
                    bullet.draw(surface, camera)
            else:
                bullet.draw(surface, camera)

    def ammo_gui(self, screen, screen_width, screen_height):
        text = self.fps_text_font.render(f" x{int(self.ammo)}", True, (255,255,255))

        ammo_image_scaled = pygame.transform.scale(self.ammo_image, (80, 80))
        
        ammo_x = 150
        ammo_y = screen_height - 100
        
        screen.blit(ammo_image_scaled, (ammo_x, ammo_y))
        screen.blit(text, (ammo_x + 70, ammo_y + 10))