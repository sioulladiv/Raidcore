import pygame, sys
from pytmx.util_pygame import load_pygame
import math
from ScreenElement import healthBar
from menu import BunkerMenu

class TiledMap:
    def __init__(self, filename):
        self.tmx_data = load_pygame(filename)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight
        
    def render_layer(self, surface, layer):
        for x, y, gid in layer:
            tile = self.tmx_data.get_tile_image_by_gid(gid)
            if tile:
                position = (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight)
                surface.blit(tile, position)
                
    def render_group_layers(self, surface, group_name):
        try:
            group = self.tmx_data.get_layer_by_name(group_name)
            for layer in group:
                if hasattr(layer, 'data'):
                    self.render_layer(surface, layer)
        except ValueError:
            print(f"Group '{group_name}' not found.")
                
    def render_all_layers(self, surface):
        for layer in self.tmx_data.layers:
            if hasattr(layer, 'data'):
                self.render_layer(surface, layer)
            elif hasattr(layer, 'layers'):
                for sublayer in layer.layers:
                    if hasattr(sublayer, 'data'):
                        self.render_layer(surface, sublayer)

    def collision_layer(self, layer_name: list):
        self.collision_tiles = []
        for layer_i in layer_name:
            layer = self.tmx_data.get_layer_by_name(layer_i)
            for x, y, gid in layer:
                tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                if tile_image:
                    self.collision_tiles.append(pygame.Rect(
                        x * self.tmx_data.tilewidth, 
                        y * self.tmx_data.tileheight, 
                        self.tmx_data.tilewidth, 
                        self.tmx_data.tileheight
                    ))
        return self.collision_tiles

    def make_map(self):
        map_surface = pygame.Surface((self.width, self.height))
        self.render_all_layers(map_surface)
        return map_surface

class Tile:
    def __init__(self, x, y, image, width=16, height=16):
        self.image = image
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, surface, camera_offset_x, camera_offset_y):
        draw_pos = (self.rect.x + camera_offset_x, self.rect.y + camera_offset_y)
        surface.blit(self.image, draw_pos)

class Lighting:
    def __init__(self, radius):
        self.radius = radius
        self.darkness = 210 
        
        self.surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        for r in range(radius):
            alpha = int((r / radius) * self.darkness)
            pygame.draw.circle(self.surface, (0, 255, 0, alpha), (radius, radius), radius - r)
            
    def update(self, player, camera):
        player_center_x = player.x + (player.width / 2)
        player_center_y = player.y + (player.height / 2)
        
        self.x = player_center_x * camera.zoom + camera.offset_x
        self.y = player_center_y * camera.zoom + camera.offset_y
        
    def draw(self, surface, camera):
        dark_overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, self.darkness))
        
        center_x = self.x
        center_y = self.y
        
        dark_overlay.blit(self.surface, (center_x - self.radius, center_y - self.radius), special_flags=pygame.BLEND_RGBA_SUB)
        
        surface.blit(dark_overlay, (0, 0))

class Camera:
    def __init__(self, width, height, zoom=1.0):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = zoom
        self.ratio = 15
    
    def update(self, target):
        target_center_x = target.x + (target.width / 2)
        target_center_y = target.y + (target.height / 2)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        real_mouse_x = (mouse_x - self.offset_x) / self.zoom
        real_mouse_y = (mouse_y - self.offset_y) / self.zoom 
        focus_x = ( self.ratio * target_center_x + real_mouse_x) / ( self.ratio+1)
        focus_y = ( self.ratio * target_center_y + real_mouse_y) /  (self.ratio+1)
        self.offset_x = self.width // 2 - int(focus_x * self.zoom)
        self.offset_y = self.height // 2 - int(focus_y * self.zoom)
    
    def apply_rect(self, rect):
        return pygame.Rect(
            int(rect.x * self.zoom) + self.offset_x,
            int(rect.y * self.zoom) + self.offset_y,
            int(rect.width * self.zoom),
            int(rect.height * self.zoom)
        )
        
    def apply_zoom(self, value):
        return int(value * self.zoom)

class Items:
    def __init__(self, x, y, item, height= 16, width=16):
        self.type = item
        self.x = x
        self.y = y
        self.height = height
        self.width = width


class Gun(Items):
    def __init__(self, x, y, type, height=70, width=70): 
        super().__init__(x, y, type, height, width)
        self.type = type
        self.ammo = 0
        self.max_ammo = 10
        self.shoot_speed = 0.5
        self.shoot_timer = 0
        self.bullet_speed = 10
        self.bullet_damage = 1
        self.bullet_radius = 5
        self.angle = 0
        self.y_offset = 5
        self.orbit_distance = 5  
        self.angle_offset = 0.15
        self.bullets = []
        self.can_shoot = True

        if self.type == "pistol":
            self.ammo = 10
            self.max_ammo = 10
            self.shoot_speed = 0.5
            self.bullet_speed = 10  
            self.bullet_damage = 1
            self.bullet_radius = 1
            self.image = pygame.image.load("./Dungeon/frames/pistol.png")
            self.image = pygame.transform.scale(self.image, (width, height))
    
    def update(self, camera=None, player=None, dt=0):
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

        for bullet in list(self.bullets):
            bullet.update(dt)
            
            if camera:
                margin = 300  
                screen_width = pygame.display.get_surface().get_width()
                screen_height = pygame.display.get_surface().get_height()
                
                min_x = (0 - camera.offset_x) / camera.zoom - margin
                min_y = (0 - camera.offset_y) / camera.zoom - margin
                max_x = (screen_width - camera.offset_x) / camera.zoom + margin
                max_y = (screen_height - camera.offset_y) / camera.zoom + margin
                
                if (bullet.x < min_x or bullet.x > max_x or 
                    bullet.y < min_y or bullet.y > max_y):
                    self.bullets.remove(bullet)

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
            self.shoot_timer = self.shoot_speed
            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_mouse_x = (mouse_x - camera.offset_x) / camera.zoom
            world_mouse_y = (mouse_y - camera.offset_y) / camera.zoom
            
            if self.pointing_left:
                self.bullet_angle = self.angle + self.angle_offset
            else:
                self.bullet_angle = self.angle - 2.2*self.angle_offset
            barrel_length = 10
            barrel_x = self.x + math.cos(self.bullet_angle) * (barrel_length-4)
            barrel_y = self.y + math.sin(self.bullet_angle) * (barrel_length-4)
            

            bullet = Bullet(
                barrel_x,
                barrel_y,
                self.angle,
                self.bullet_speed,
                self.bullet_damage,
                self.bullet_radius
            )
            self.bullets.append(bullet)
        
        # Draw all bullets
        for bullet in self.bullets:
            bullet.draw(surface, camera)

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
        
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 50  
        
        self.trail.append((self.x, self.y))
        self.animation = []
        for i in range(20):
            img = pygame.image.load(f"./Dungeon/frames/bullet{'0' + str(i) if i < 10 else str(i)}.png")
            img = pygame.transform.scale(img, (radius * 4, radius * 4))  
            self.animation.append(img)
        
    def update(self, dt=16):  
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        # Update trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
            
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.animation)
            self.animation_timer = 0

    def draw(self, surface, camera):
        for i, (trail_x, trail_y) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            
            screen_x = trail_x * camera.zoom + camera.offset_x
            screen_y = trail_y * camera.zoom + camera.offset_y
            
            size = max(1, int(self.radius * (i / len(self.trail)) * camera.zoom))
            
            pygame.draw.circle(surface, (255, i * 50, 0), (int(screen_x), int(screen_y)), size)
        
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

class Player:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.speed = 3
        self.color = (255, 0, 0)
        self.width = width
        self.height = height
        
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 80 
        self.is_moving = False
        self.facing_dir = 0

        self.collision_width = int(width * 0.7)
        self.collision_height = int(height * 0.6)
        self.collision_offset_x = (width - self.collision_width) // 2
        self.collision_offset_y = height - self.collision_height - 2

        self.idle_frames = []
        for i in range(21):
            img = pygame.image.load(f"./Dungeon/frames/agent_idle{'0' + str(i) if i < 10 else str(i)}.png")
            img = pygame.transform.scale(img, (width, height))
            self.idle_frames.append(img)  
            self.idle_frames.append(img)  

        self.walk_frames = []
        for i in range(4):
            img = pygame.image.load(f"./Dungeon/frames/agent_running{i}.png")
            img = pygame.transform.scale(img, (width, height))
            self.walk_frames.append(img)

    def update(self, keys, tiles):
        self.is_moving = False
        dx, dy = 0, 0
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        player_center_x = self.x + (self.width / 2)
        player_center_y = self.y + (self.height / 2)
        
        camera = pygame.Surface.get_rect(pygame.display.get_surface()).center
        
        if mouse_x < camera[0]:  
            self.facing_dir = 0  
        else:
            self.facing_dir = 1  
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            self.is_moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.is_moving = True
            
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
            self.is_moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            self.is_moving = True

        # when going diagonally reduce speed otherwise going diagonal speeds up the player
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        
        self.move_and_collide(dx, dy, tiles)

    def move_and_collide(self, dx, dy, tiles):
        self.x += dx
        player_rect = self.get_rect(self.x, self.y)
        
        for wall in tiles:
            if player_rect.colliderect(wall):
                if dx > 0: 
                    self.x = wall.left - self.collision_width - self.collision_offset_x
                elif dx < 0: 
                    self.x = wall.right - self.collision_offset_x
                break
                
        self.y += dy
        player_rect = self.get_rect(self.x, self.y)
        
        for wall in tiles:
            if player_rect.colliderect(wall):
                if dy > 0:  
                    self.y = wall.top - self.collision_height - self.collision_offset_y
                elif dy < 0:  
                    self.y = wall.bottom - self.collision_offset_y
                break

    def get_rect(self, x, y):
        return pygame.Rect(
            x + self.collision_offset_x,
            y + self.collision_offset_y,
            self.collision_width,
            self.collision_height
        )

    def update_animation(self, dt):
        self.animation_timer += dt
        
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            
            if self.is_moving:
                self.current_frame = (self.current_frame + 1) % max(1, len(self.walk_frames))
            else:
                self.current_frame = (self.current_frame + 1) % max(1, len(self.idle_frames))

    def draw(self, surface, camera=None):
        if self.is_moving:
            current_img = self.walk_frames[self.current_frame % len(self.walk_frames)]
            if self.facing_dir == 0:  
                current_img = pygame.transform.flip(current_img, True, False)
        else:
            current_img = self.idle_frames[self.current_frame % len(self.idle_frames)]
            if self.facing_dir == 0:
                current_img = pygame.transform.flip(current_img, True, False)
        
        if camera:
            draw_x = self.x * camera.zoom + camera.offset_x
            draw_y = self.y * camera.zoom + camera.offset_y
            scaled_img = pygame.transform.scale(
                current_img, 
                (int(self.width * camera.zoom), int(self.height * camera.zoom))
            )
            surface.blit(scaled_img, (draw_x, draw_y))
        else:
            surface.blit(current_img, (self.x, self.y))

def run_game():
    pygame.init()
    screen_width, screen_height = 2560, 1440
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Tiled Map Example")
    
    FPS = 60
    health_bar = healthBar(50, 50, 100, 100)
    health_bar.update(100)  
    light = Lighting(350)
    game_map = TiledMap("./Tiled/level1.tmx")
    map_surface = game_map.make_map()
    collision_tiles = game_map.collision_layer(["wall lining","wall lining2"])
    
    gun = Gun(0, 0, "pistol")
    player_x = game_map.width // 2
    player_y = game_map.height // 2
    player = Player(player_x, player_y, 16, 28, (255, 0, 0))
    zoom_level = 8 
    camera = Camera(screen_width, screen_height, zoom_level)
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(FPS)
        gun.update(camera, player, dt) 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        player.update_animation(dt)
        health_bar.update_animation(dt) 
        
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_t]:
            health_bar.damage(2)  
            
        player.update(keys, collision_tiles)  
        camera.update(player)
        light.update(player, camera)
        
        screen.fill((90, 90, 90))
        
        scaled_width = int(map_surface.get_width() * camera.zoom)
        scaled_height = int(map_surface.get_height() * camera.zoom)
        if camera.zoom != 1.0:
            scaled_surface = pygame.transform.scale(map_surface, (scaled_width, scaled_height))
            screen.blit(scaled_surface, (camera.offset_x, camera.offset_y))
        else:
            screen.blit(map_surface, (camera.offset_x, camera.offset_y))
        
        player.draw(screen, camera)
        light.draw(screen, camera)
        gun.draw(screen, camera, player, dt) 

        health_bar.draw(screen)  

        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    menu = BunkerMenu(2560, 1440)
    menu_result = menu.run()
    
    if menu_result == "start_game":
        run_game()
    elif menu_result == "continue":
        run_game()
    elif menu_result == "options":
        print("not done yet")
    else: 
        print("Exiting game")
