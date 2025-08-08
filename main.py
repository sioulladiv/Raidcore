import pygame, sys
from pytmx.util_pygame import load_pygame
import math
from ScreenElement import healthBar
from menu import BunkerMenu
import json
import os
import random

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement


with open("enemy_data.json", "r") as f:
    enemy_data = json.load(f)

tile_size = 16


class Game:
    def __init__(self, screen_width, screen_height, zoom_level=1.0):  # Fixed typo in __init_
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom_level = zoom_level
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.level = 1
        pygame.display.set_caption("Dungeon Game")
        
        self.game_map = TiledMap("Tiled/level{}.tmx".format(self.level))
        self.camera = Camera(screen_width, screen_height, zoom_level)
        
        self.player = Player(100, 100, 32, 32, (0, 255, 0))
        self.enemies = []
        self.bullets = []
        
        self.light = Lighting(200)
         
        self.health_bar = healthBar(10, 10, 400, 80)
        
        # Add player damage cooldown
        self.player_damage_cooldown = 0
        self.player_damage_cooldown_duration = 60  # 1 second at 60 FPS
        
        self.menu = BunkerMenu(self.screen_width // 2 - 150, self.screen_height // 2 - 150)
        self.transition_timer = 0

        self.lightlevel = 210
        
        self.fade_overlay_alpha = 0
        self.fade_overlay_duration = 1000  
        self.fade_overlay_timer = 0
        self.fade_overlay_active = False

        self.press_e_image = pygame.image.load("Assets/press_e.png")
        self.press_e_image = pygame.transform.scale(self.press_e_image, (240, 192))  
        self.show_press_e = False
        self.path_grid = self.make_path_grid()
        print(self.path_grid)  

        # Add book overlay properties
        self.book_image = pygame.image.load("Assets/book.png")
        book_width = screen_width - 200  # Leave 100px margin on each side
        book_height = screen_height - 200  # Leave 100px margin on top/bottom
        self.book_image = pygame.transform.scale(self.book_image, (book_width, book_height))
        self.show_book = False
        self.book_x = 100  # Center position
        self.book_y = 100

    def run(self):
        pygame.init()
        screen_width, screen_height = 2560, 1440
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Dungeon Escape")

        FPS = 60
        # Use the health_bar from the Game class instead of creating a new one
        health_bar = self.health_bar
        health_bar.update(100)  
        light = Lighting(350)
        map_surface = self.game_map.make_map()
        try:
            collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining2"])
        except Exception as e:
            collision_tiles = self.game_map.collision_layer(["wall lining"])

        gun = Gun(0, 0, "pistol")
        player_x = self.game_map.width // 2
        player_y = self.game_map.height // 2
        self.player = Player(player_x, player_y, 16, 28, (255, 0, 0))

        # Load enemies for current level into self.enemies
        self.load_enemies_for_level(self.enemies)

        #for i in range(2): 
        #    enemy_type = "chort"
         #   data = enemy_data[enemy_type]
        #    enemies.append(Enemy(player_x + (50 * i), player_y + (50 * i), enemy_type))

        zoom_level = 8 
        camera = Camera(screen_width, screen_height, zoom_level)
        clock = pygame.time.Clock()
        running = True

        map_surface = self.game_map.make_map()
        try:
            collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining2"])
        except Exception as e:
            collision_tiles = self.game_map.collision_layer(["wall lining"])
        endlevel_tiles = self.game_map.endlevel_layer("endlevel")

        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)

        while running:
            dt = clock.tick(FPS)
            
            # Update player damage cooldown
            if self.player_damage_cooldown > 0:
                self.player_damage_cooldown -= 1
            
            gun.update(camera, self.player, dt, collision_tiles) 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        if self.show_book:
                            self.show_book = False
                        elif self.show_press_e:
                            for chest in self.chests:
                                if chest.is_near_player(self.player):
                                    self.show_book = True
                                    break
                            
            self.player.update_animation(dt)
            health_bar.update_animation(dt) 

            keys = pygame.key.get_pressed()
# Test with larger damage to see effect

            if not self.show_book:
                self.player.update(keys, collision_tiles, endlevel_tiles, self)
                camera.update(self.player)
                light.update(self.player, camera, self.lightlevel)

                self.show_press_e = False
                for chest in self.chests:
                    if chest.is_near_player(self.player):
                        self.show_press_e = True

                # Check for player-enemy collisions
                player_rect = self.player.get_rect(self.player.x, self.player.y)
                for enemy in self.enemies:
                    enemy_rect = enemy.get_rect(enemy.x, enemy.y)
                    if player_rect.colliderect(enemy_rect) and self.player_damage_cooldown <= 0:
                        health_bar.damage(20)  # Increase damage to make it more visible
                        self.player_damage_cooldown = self.player_damage_cooldown_duration
                        print(f"Enemy collision! Health: {health_bar.life}")
                        break

                for enemy in list(self.enemies): 
                    enemy.update(keys, collision_tiles, self.player, self.enemies, self.path_grid, gun.bullets, health_bar) 
                    enemy.update_animation(dt)

            if self.fade_overlay_active:
                self.fade_overlay_timer += dt
                progress = self.fade_overlay_timer / self.fade_overlay_duration
                if progress >= 1.0:
                    self.fade_overlay_active = False
                    self.fade_overlay_alpha = 0
                else:
                    self.fade_overlay_alpha = int(255 * (1 - progress))

            screen.fill((90, 90, 90))

            scaled_width = int(map_surface.get_width() * camera.zoom)
            scaled_height = int(map_surface.get_height() * camera.zoom)
            if camera.zoom != 1.0:
                scaled_surface = pygame.transform.scale(map_surface, (scaled_width, scaled_height))
                screen.blit(scaled_surface, (camera.offset_x, camera.offset_y))
            else:
                screen.blit(map_surface, (camera.offset_x, camera.offset_y))

            self.player.draw(screen, camera)


            for enemy in self.enemies:
                enemy.draw(screen, camera)

            light.draw(screen, camera)
            gun.draw(screen, camera, self.player, dt)

            health_bar.draw(screen)  

            if self.show_press_e and not self.show_book:
                prompt_x = 40  
                prompt_y = screen_height - 300  
                screen.blit(self.press_e_image, (prompt_x, prompt_y))

            if self.show_book:
                screen.blit(self.book_image, (self.book_x, self.book_y))

            if self.fade_overlay_active and self.fade_overlay_alpha > 0:
                fade_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
                fade_surface.fill((0, 0, 0, self.fade_overlay_alpha))
                screen.blit(fade_surface, (0, 0))

            pygame.display.flip()

            if map_surface != self.game_map.make_map():
                map_surface = self.game_map.make_map()
                try:
                    collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining2"])
                except Exception as e:
                    collision_tiles = self.game_map.collision_layer(["wall lining"])
                endlevel_tiles = self.game_map.endlevel_layer("endlevel")

        pygame.quit()

    def next_level(self):

        self.enemies.clear()
        self.player.x = 100
        self.player.y = 100
        self.camera.offset_x = 0
        self.camera.offset_y = 0
        self.camera.zoom = 1.0
        
        self.camera.width = self.screen_width
        self.camera.height = self.screen_height
        self.level_transition()


    def level_transition(self):
        self.transition_timer = 500
        fade_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        clock = pygame.time.Clock() 

        fade_out_duration = 1000 
        fade_out_start = pygame.time.get_ticks()
        while True:
            dt = clock.tick(60) 
            elapsed = pygame.time.get_ticks() - fade_out_start
            if elapsed > fade_out_duration:
                break
            
            progress = elapsed / fade_out_duration
            alpha = int(255 * (progress ** 0.5))  
            
            fade_surface.fill((0, 0, 0, alpha))
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.flip()

        self.level += 1
        print("Transitioning from level {} to {}".format(self.level-1, self.level))
        next_level_path = f"Tiled/level{self.level}.tmx"
        print(next_level_path)

        try:
            self.game_map = TiledMap(next_level_path)
            self.path_grid = self.make_path_grid()
        except FileNotFoundError:
            print(f"No more levels. File not found: {next_level_path}")
            return

        self.player.x = self.game_map.width // 2 - self.player.width // 2
        self.player.y = self.game_map.height // 2 - self.player.height // 2

        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)

        self.enemies.clear()
        self.load_enemies_for_level(self.enemies)

        self.zoom_level = 8.0
        self.camera.zoom = self.zoom_level
        self.camera.update(self.player)

        self.fade_overlay_active = True
        self.fade_overlay_alpha = 255
        self.fade_overlay_timer = 0

    def spawn_enemy(self, x, y, enemy_type):
        data = enemy_data[enemy_type]
        enemy = Enemy(x, y, enemy_type)
        self.enemies.append(enemy)
       
    def load_enemies_for_level(self, enemies_list):
        level_key = f"level{self.level}"
        for enemy_type, data in enemy_data.items():
            if "spawn_locations" in data and level_key in data["spawn_locations"]:
                for spawn_point in data["spawn_locations"][level_key]:
                    enemy = Enemy(spawn_point["x"], spawn_point["y"], enemy_type)
                    enemies_list.append(enemy)
                    print(f"Spawned {enemy_type} at ({spawn_point['x']}, {spawn_point['y']})")

        #for i in range(2): 
        #    enemy_type = "chort"
         #   data = enemy_data[enemy_type]
        #    enemies.append(Enemy(player_x + (50 * i), player_y + (50 * i), enemy_type))
        
    def make_path_grid(self):
        walkable_tiles = []
        enemy_width_tiles = 1  
        enemy_height_tiles = 2  

        for y in range(self.game_map.tmx_data.height):
            row = []
            for x in range(self.game_map.tmx_data.width):
                blocked = False

                # Check if this tile or surrounding tiles (for enemy size) are blocked
                for check_y in range(max(0, y), min(self.game_map.tmx_data.height, y + enemy_height_tiles)):
                    for check_x in range(max(0, x), min(self.game_map.tmx_data.width, x + enemy_width_tiles)):
                        try:
                            for layer_name in ["wall lining", "wall lining2"]:
                                layer = self.game_map.tmx_data.get_layer_by_name(layer_name)
                                tile_grid = layer.data[check_y][check_x]
                                if tile_grid:
                                    blocked = True
                                    break
                            if blocked:
                                break
                        except:
                            try:
                                layer = self.game_map.tmx_data.get_layer_by_name("wall lining")
                                tile_grid = layer.data[check_y][check_x]
                                if tile_grid:
                                    blocked = True
                                    break
                            except:
                                pass
                    if blocked:
                        break
                    
                row.append(1 if not blocked else 0)
            walkable_tiles.append(row)
        return walkable_tiles

    def lose_life(self):
        if hasattr(self, 'health_bar'):
            self.health_bar.damage(0.5)  # Increase damage amount
            print(f"Player health: {self.health_bar.life}")

class Enemy:
    def __init__(self, x, y, Ennemytype='chort'):
        data = enemy_data[Ennemytype]
        self.x = x
        self.y = y
        self.width = data["width"]
        self.height = data["height"]
        self.speed = data["speed"]
        self.lives = data["lives"]
        self.color = (255, 0, 0)
        self.hit_timer = 0
        self.type = Ennemytype
        self.detection_range = data["detection_range"]
        self.path_find_timer = 0
        self.path_arr_index = 0
        self.collision_slowdown_timer = 0
        self.original_speed = self.speed
        
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = data["animations"]["idle"]["frames"] * 20
        self.is_moving = False
        self.facing_dir = 0
        self.collision_width = int(self.width * 0.7)
        self.collision_height = int(self.height * 0.6)
        self.collision_offset_x = (self.width - self.collision_width) // 2
        self.collision_offset_y = self.height - self.collision_height - 2

        self.health_bar = healthBar(x, y - 20, self.width, 10)
    
        self.idle_frames = []
        for i in range(data["animations"]["idle"]["frames"]):
            img = pygame.image.load(f"{data['frame_path']}_idle_anim_f{i}.png")
            img = pygame.transform.scale(img, (self.width, self.height))
            self.idle_frames.append(img)

        self.walk_frames = []
        for i in range(data["animations"]["run"]["frames"]):
            img = pygame.image.load(f"{data['frame_path']}_run_anim_f{i}.png")
            img = pygame.transform.scale(img, (self.width, self.height))
            self.walk_frames.append(img)

        # Add damage cooldown timer
        self.damage_cooldown_timer = 0
        self.damage_cooldown_duration = 60  # 1 second at 60 FPS

    def update_pathfinding(self, player, collision_grid):
        if not hasattr(self, 'path'):
            self.path = []
            self.path_arr_index = 0

        self.path_find_timer = 0
        grid = Grid(matrix=collision_grid)
        start_x = int((self.x + self.width // 2) // 16)
        start_y = int((self.y + self.height // 2) // 16)
        end_x = int((player.x + player.width // 2) // 16)
        end_y = int((player.y + player.height // 2) // 16)

        grid_width = len(collision_grid[0])
        grid_height = len(collision_grid)
        start_x = max(0, min(start_x, grid_width - 1))
        start_y = max(0, min(start_y, grid_height - 1))
        end_x = max(0, min(end_x, grid_width - 1))
        end_y = max(0, min(end_y, grid_height - 1))

        if (0 <= start_x < grid_width and
            0 <= start_y < grid_height and
            0 <= end_x < grid_width and
            0 <= end_y < grid_height):
            start = grid.node(start_x, start_y)
            end = grid.node(end_x, end_y)
            finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
            path, _ = finder.find_path(start, end, grid)
            if path and len(path) > 1:  
                self.path = path
                self.path_arr_index = 0
            

    def update(self, keys, tiles, player, enemies, collision_grid, bullets=None, health_bar=None): 
        self.path_find_timer += 1
        distance_to_player = ((player.x - self.x) ** 2 + (player.y - self.y) ** 2) ** 0.5


        if hasattr(self, 'collision_slowdown_timer') and self.collision_slowdown_timer > 0:
            self.collision_slowdown_timer -= 1
            if self.collision_slowdown_timer <= 0:
                self.speed = self.original_speed

        if not hasattr(self, 'path') or self.path is None:
            self.path = []
            self.path_arr_index = 0

        if self.path_find_timer % 30 == 0:  
            self.update_pathfinding(player, collision_grid)

        if self.hit_timer > 0:
            self.hit_timer -= 1  
            if self.hit_timer < 0:
                self.hit_timer = 0 

        if not self.path or self.path_arr_index >= len(self.path):
            return

        tile_x, tile_y = self.path[self.path_arr_index]

        target_x = tile_x * tile_size + tile_size // 2
        target_y = tile_y * tile_size + tile_size // 2

        direction_x = target_x - (self.x + self.width // 2) 
        direction_y = target_y - (self.y + self.height // 2)

        if (direction_x) ** 2 + (direction_y) ** 2 < 25:  
            self.path_arr_index += 1
            if self.path_arr_index >= len(self.path):
                self.path_arr_index = len(self.path) - 1 
                return

        self.is_moving = False

        if distance_to_player < self.detection_range and (direction_x ** 2 + direction_y ** 2) ** 0.5 > 0:
            self.is_moving = True

            distance = (direction_x ** 2 + direction_y ** 2) ** 0.5
            direction_x /= distance
            direction_y /= distance

            dx = direction_x * self.speed 
            dy = direction_y * self.speed 

            if direction_x > 0:
                self.facing_dir = 1  
            else:
                self.facing_dir = 0

            self.move_and_collide(dx, dy, tiles, enemies, bullets, player, health_bar)

    def move_and_collide(self, dx, dy, tiles, enemies=None, bullets=None, player=None, health_bar=None):
        self.x += dx
        enemy_rect = self.get_rect(self.x, self.y)
        
        for wall in tiles:
            if enemy_rect.colliderect(wall):
                if dx > 0: 
                    self.x = wall.left - self.collision_width - self.collision_offset_x
                elif dx < 0: 
                    self.x = wall.right - self.collision_offset_x
                break
                
        self.y += dy
        enemy_rect = self.get_rect(self.x, self.y)
        
        for wall in tiles:
            if enemy_rect.colliderect(wall):
                if dy > 0:  
                    self.y = wall.top - self.collision_height - self.collision_offset_y
                elif dy < 0:  
                    self.y = wall.bottom - self.collision_offset_y
                break

        if bullets:
            for bullet in list(bullets):  
                if enemy_rect.colliderect(bullet.get_rect()) and bullet.alive:  
                    self.hit_timer = 10  
                    self.lives -= bullet.damage
                    bullet.alive = False  
                    if self.lives <= 0 and enemies is not None:
                        enemies.remove(self)
                        break  

        if enemies:
            for other_enemy in enemies:
                if other_enemy != self:  
                    other_rect = other_enemy.get_rect(other_enemy.x, other_enemy.y)
                    if enemy_rect.colliderect(other_rect):
                        last_enemy = enemies[-1] if enemies else None

                        if last_enemy:
                            if not hasattr(last_enemy, 'original_speed'):
                                last_enemy.original_speed = last_enemy.speed
                            last_enemy.speed = last_enemy.original_speed * 0.3 
                            last_enemy.collision_slowdown_timer = 120  

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
        if self.hit_timer > 0:
            self.speed = 1.2
        else:
            self.speed = enemy_data[self.type]['speed']
        if self.hit_timer > 6:
            current_img = current_img.copy()
            current_img.fill((255, 255, 255), special_flags=pygame.BLEND_ADD)
            current_img.fill((255, 255, 255, 200), special_flags=pygame.BLEND_RGBA_MULT)
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
    
    def endlevel_layer(self, layer_name: str):
        self.endlevel_tiles = []
        layer = self.tmx_data.get_layer_by_name(layer_name)
        for x, y, gid in layer:
            tile_image = self.tmx_data.get_tile_image_by_gid(gid)
            if tile_image:
                self.endlevel_tiles.append(pygame.Rect(
                    x * self.tmx_data.tilewidth, 
                    y * self.tmx_data.tileheight, 
                    self.tmx_data.tilewidth, 
                    self.tmx_data.tileheight
                ))
        return self.endlevel_tiles

    def chests_layer(self, layer_name: str):
        self.chest_tiles = []
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
            for x, y, gid in layer:
                tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                if tile_image:
                    self.chest_tiles.append({
                        'x': x * self.tmx_data.tilewidth,
                        'y': y * self.tmx_data.tileheight,
                        'type': 'treasure'  
                    })
        except ValueError:
            print(f"Chest layer '{layer_name}' not found.")
        return self.chest_tiles

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
    def __init__(self, radius, darkness=210):
        self.radius = radius
        self.darkness = darkness

        self.surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        for r in range(radius):
            alpha = int((r / radius) * self.darkness)
            pygame.draw.circle(self.surface, (0, 255, 0, alpha), (radius, radius), radius - r)

    def update(self, player, camera, darkness=210):
        self.darkness = darkness

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
    def __init__(self, x, y, type, height=122, width=70): 
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
        self.angle_offset = 0

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

        for bullet in list(self.bullets):
            bullet.update(dt, collision_tiles)
            
            # Remove bullets that are completely dead (no trail left)
            if bullet.is_completely_dead():
                self.bullets.remove(bullet)
                continue
            
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

class Chest:
    def __init__(self, x, y, task_type, height=32, width=32):
        self.type = task_type
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.proximity_distance = 32
        self.interaction_distance = 32

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_distance_to_player(self, player):
        chest_center_x = self.x + self.width // 2
        chest_center_y = self.y + self.height // 2
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        
        dx = chest_center_x - player_center_x
        dy = chest_center_y - player_center_y
        return math.sqrt(dx * dx + dy * dy)

    def is_near_player(self, player):
        return self.get_distance_to_player(player) <= self.proximity_distance

    def is_touching_player(self, player):
        return self.get_distance_to_player(player) <= self.interaction_distance

    def update(self, player, dt, keys=None):
        return False

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

    def update(self, keys, tiles,endlevel_tiles, game): 
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

        for tile in endlevel_tiles:
            if self.get_rect(self.x, self.y).colliderect(tile):
                print("next level")
                game.next_level()

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

        
        for enemy in game.enemies:
            if player_rect.colliderect(enemy.get_rect(enemy.x, enemy.y)):
                game.lose_life()
                print("Player hit by enemy!")
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

if __name__ == "__main__":
    menu = BunkerMenu(2560, 1440)
    menu_result = menu.run()
    game = Game(2560, 1440, zoom_level=1.0)
    
    if menu_result == "start_game":
        game.run()
    elif menu_result == "continue":
        game.run()
    elif menu_result == "options":
        print("not done yet")
    else: 
        print("Exiting game")
        game.run()
