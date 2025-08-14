import pygame, sys
from pytmx.util_pygame import load_pygame
import math
from ui.menu import BunkerMenu
from entities.enemy import Enemy
from entities.player import Player  
from entities.particle import Particle
from world.tilemap import TiledMap, Tile
from world.lighting import Lighting
from world.camera import Camera
from world.chest import Chest
from weapons.gun import Gun
from weapons.bullet import Bullet
from ui.health_bar import HealthBar
from ui.game_over import GameOverScreen
from ui.music import Music
from ui.level_logic import level2
from world.lever import Lever

import json
import os
import random



with open("data/enemy_data.json", "r") as f:
    enemy_data = json.load(f)

tile_size = 16


class Game:
    def __init__(self, screen_width, screen_height, zoom_level=1.0): 
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom_level = zoom_level
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.level = 1
        pygame.display.set_caption("Dungeon Game")

        self.game_map = TiledMap("Tiled/level{}.tmx".format(self.level))
        self.game_map.set_current_level(self.level)
        
        self.camera = Camera(screen_width, screen_height, zoom_level)
        
        self.player = Player(100, 100, 32, 32, (0, 255, 0))
        self.enemies = []
        self.bullets = []
        self.music = Music()
        self.light = Lighting(200)

        self.health_bar = HealthBar(10, 10, 400, 80)
        self.level2 = level2()

        self.player_damage_cooldown = 0
        self.player_damage_cooldown_duration = 60 
        
        self.menu = BunkerMenu(self.screen_width // 2 - 150, self.screen_height // 2 - 150)
        self.transition_timer = 0

        self.lightlevel = 240

        self.chest_sounds = {
            "open": "Assets/Sounds/chest_open.mp3",
            "close": "Assets/Sounds/chest_close.mp3"
        }
        self.player_sounds = {
            "hurt" : "Assets/Sounds/Player/player_hurt.mp3",
            "death" : "Assets/Sounds/Player/player_death.mp3"
        }

        self.lever_sound = pygame.mixer.Sound("Assets/Sounds/Pressure_plate.mp3")
        self.spike_retract = pygame.mixer.Sound("Assets/Sounds/spikes_retract.mp3")


        self.chest_sounds["open"] = pygame.mixer.Sound(self.chest_sounds["open"])
        self.chest_sounds["close"] = pygame.mixer.Sound(self.chest_sounds["close"])
        
        self.player_sounds["hurt"] = pygame.mixer.Sound(self.player_sounds["hurt"])
        self.player_sounds["death"] = pygame.mixer.Sound(self.player_sounds["death"])

        self.fade_overlay_alpha = 0
        self.fade_overlay_duration = 1000  
        self.fade_overlay_timer = 0
        self.fade_overlay_active = False

        self.levers = {1: False, 2: False, 3: False, 4: False}

        self.press_e_image = pygame.image.load("Assets/press_e.png")
        self.press_e_image = pygame.transform.scale(self.press_e_image, (240, 192))  
        self.show_press_e = False
        self.path_grid = self.make_path_grid()
        print(self.path_grid)  

        # Load letter animation frames
        self.letter_frames = []
        letter_folder = "Assets/letter_animation"
        if os.path.exists(letter_folder):
            frame_files = sorted([f for f in os.listdir(letter_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])
            for frame_file in frame_files:
                frame_path = os.path.join(letter_folder, frame_file)
                frame_image = pygame.image.load(frame_path)
                
                # Calculate scaling to fill screen while maintaining 240:180 aspect ratio
                original_ratio = 240 / 180  # 4:3 ratio
                scale_x = screen_width / 240
                scale_y = screen_height / 180
                scale = min(scale_x, scale_y) * 0.8  # Use 80% of screen to leave some margin
                
                new_width = int(240 * scale)
                new_height = int(180 * scale)
                frame_image = pygame.transform.scale(frame_image, (new_width, new_height))
                self.letter_frames.append(frame_image)
        
        self.show_letter = False
        self.letter_frame_index = 0
        self.letter_animation_timer = 0
        self.letter_animation_speed = 100  # milliseconds per frame
        self.letter_animation_complete = False
        # Center the letter on screen
        if self.letter_frames:
            self.letter_x = (screen_width - self.letter_frames[0].get_width()) // 2
            self.letter_y = (screen_height - self.letter_frames[0].get_height()) // 2
        else:
            self.letter_x = 100
            self.letter_y = 100

        self.game_over_screen = GameOverScreen(screen_width, screen_height)
        self.game_over = False
        self.death_sound_played = False
        self.spikes_deactivated_sound_played = False  # Track if spike retract sound has been played


    def run(self):
        pygame.init()
        screen_width, screen_height = 2560, 1440
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Dungeon Escape")
    
        FPS = 60
        health_bar = self.health_bar
        health_bar.update(100)  
        light = Lighting(350)
        
        try:
            collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining2"])
            spike_tiles = self.game_map.collision_layer(["spikes"])
        except Exception as e:
            collision_tiles = self.game_map.collision_layer(["wall lining"])
            spike_tiles = self.game_map.collision_layer(["spikes"])

        endlevel_tiles = self.game_map.endlevel_layer("endlevel")
    
        gun = Gun(0, 0, "pistol")
        player_x = self.game_map.width // 2
        player_y = self.game_map.height // 2
        self.player = Player(player_x, player_y, 16, 28, (255, 0, 0))
    
        self.load_enemies_for_level(self.enemies)
    
        zoom_level = 10 
        camera = Camera(screen_width, screen_height, zoom_level)
        clock = pygame.time.Clock()
        running = True
        self.particles = []
    
        map_surface = self.game_map.make_map()
    
        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)

        lever_data = self.game_map.lever_layer("levers")
        self.lever_objects = []  
        for i, lever_info in enumerate(lever_data):
            lever_id = f"lever{i+1}" 
            lever = Lever(lever_info['x'], lever_info['y'], lever_info['type'], lever_id=lever_id)
            self.lever_objects.append(lever)

    
        while running:
            self.life = self.health_bar.life
            if self.life <= 0 and not self.game_over:
                self.game_over = True
                if not self.death_sound_played:
                    self.player_sounds["death"].play()
                    self.death_sound_played = True
                self.music.play_game_over_music()
            dt = clock.tick(FPS)
            
            if self.player_damage_cooldown > 0:
                self.player_damage_cooldown -= 1

            if not self.game_over:
                self.music.update(self.level)
            
            gun.update(camera, self.player, dt, collision_tiles) 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif self.game_over:
                    result = self.game_over_screen.handle_events([event])
                    if result == "restart":
                        self.restart_game()
                    elif result == "quit":
                        running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        if self.level == 1:
                            if self.show_letter:
                                self.chest_sounds["close"].play()
                                self.show_letter = False
                                self.letter_animation_complete = False
                                self.letter_frame_index = 0
                                self.letter_animation_timer = 0
                            elif self.show_press_e:
                                for chest in self.chests:
                                    if chest.is_near_player(self.player):
                                        self.show_letter = True
                                        self.chest_sounds["open"].play()
                                        self.letter_frame_index = 0
                                        self.letter_animation_timer = 0
                                        self.letter_animation_complete = False
                                        break
                        elif self.level == 2:
                            if self.level2.all_levers_pulled:
                                break
                            else:
                                for i, lever in enumerate(self.lever_objects):
                                    if lever.is_near_player(self.player) and not lever.is_pulled:
                                        if lever.pull(): 
                                            lever_number = i + 1
                                            self.levers[lever_number] = True
                                            lever_id = lever.lever_id or f"lever{lever_number}"
                                            if self.level2.pull_lever(lever_id):
                                                self.game_map.update_lever_state(lever_id, True)
                                                self.lever_sound.play()  
                                                print(f"Pulled {lever_id}")
                                        break

            self.player.update_animation(dt)
            health_bar.update_animation(dt) 

            keys = pygame.key.get_pressed()

            if not self.show_letter and not self.game_over:
                self.player.update(keys, collision_tiles, endlevel_tiles, self, spike_tiles)
                camera.update(self.player)
                light.update(self.player, camera, self.lightlevel)

                self.show_press_e = False
                
                # Check for chest proximity on level 1
                if self.level == 1:
                    for chest in self.chests:
                        if chest.is_near_player(self.player):
                            self.show_press_e = True
                            break
                
                # Check for lever proximity on level 2
                elif self.level == 2:
                    for lever in self.lever_objects:
                        if lever.is_near_player(self.player) and not lever.is_pulled:
                            self.show_press_e = True
                            break

                for enemy in list(self.enemies): 
                    enemy.update(keys, collision_tiles, self.player, self.enemies, self.path_grid, gun.bullets, health_bar, self.particles) 
                    enemy.update_animation(dt)

            if self.fade_overlay_active:
                self.fade_overlay_timer += dt
                progress = self.fade_overlay_timer / self.fade_overlay_duration
                if progress >= 1.0:
                    self.fade_overlay_active = False
                    self.fade_overlay_alpha = 0
                else:
                    self.fade_overlay_alpha = int(255 * (1 - progress))

            screen.fill((0, 0, 0))

            # Update letter animation
            if self.show_letter and not self.letter_animation_complete and len(self.letter_frames) > 0:
                self.letter_animation_timer += dt
                if self.letter_animation_timer >= self.letter_animation_speed:
                    self.letter_animation_timer = 0
                    self.letter_frame_index += 1
                    if self.letter_frame_index >= len(self.letter_frames):
                        self.letter_frame_index = len(self.letter_frames) - 1
                        self.letter_animation_complete = True

            for particle in list(self.particles):
                particle.update(dt)
                if particle.is_dead():
                    self.particles.remove(particle)

            map_screen_x = camera.offset_x
            map_screen_y = camera.offset_y
            map_screen_width = int(self.game_map.width * camera.zoom)
            map_screen_height = int(self.game_map.height * camera.zoom)

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

            for particle in self.particles:
                particle.draw(screen, camera)

            light.draw(screen, camera)
            gun.draw(screen, camera, self.player, dt)

            health_bar.draw(screen)

            if self.show_press_e and not self.show_letter:
                prompt_x = 40  
                prompt_y = screen_height - 300  
                screen.blit(self.press_e_image, (prompt_x, prompt_y))

            if self.show_letter and len(self.letter_frames) > 0:
                current_frame = self.letter_frames[self.letter_frame_index]
                screen.blit(current_frame, (self.letter_x, self.letter_y))

            if self.fade_overlay_active and self.fade_overlay_alpha > 0:
                fade_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
                fade_surface.fill((0, 0, 0, self.fade_overlay_alpha))
                screen.blit(fade_surface, (0, 0))

            if self.game_over:
                self.game_over_screen.draw(screen,self.level)

            pygame.display.flip()

            if self.level == 2:
                previous_all_levers_pulled = self.level2.all_levers_pulled
                self.level2.update()
                self.game_map.set_all_levers_pulled(self.level2.all_levers_pulled)
                
                # Play spike retract sound when all levers are first pulled
                if not previous_all_levers_pulled and self.level2.all_levers_pulled and not self.spikes_deactivated_sound_played:
                    self.spike_retract.play()
                    self.spikes_deactivated_sound_played = True

            if map_surface != self.game_map.make_map():
                map_surface = self.game_map.make_map()
                try:
                    collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining2"])
                    # Load spikes for all levels, but handle level 2 spike logic separately
                    if self.level == 2:
                        # Always load spikes layer for collision, but check lever state for damage
                        spike_tiles = self.game_map.collision_layer(["spikes"])
                        if self.level2.all_levers_pulled:
                            spike_tiles = []  # Disable spikes when all levers are pulled
                except Exception as e:
                    collision_tiles = self.game_map.collision_layer(["wall lining"])
                    spike_tiles = []
                endlevel_tiles = self.game_map.endlevel_layer("endlevel")



        pygame.quit()

    def next_level(self):
        self.enemies.clear()
        self.particles.clear()
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
            self.game_map.set_current_level(self.level)
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
        self.music.play_level_music(self.level)

        self.fade_overlay_active = True
        self.fade_overlay_alpha = 255
        self.fade_overlay_timer = 0

        # Reset lever states for new level
        if self.level == 2:
            self.level2 = level2()
            self.levers = {1: False, 2: False, 3: False, 4: False}  # Reset dictionary
            self.game_map.set_all_levers_pulled(False)  # Reset spikes2 visibility
            self.spikes_deactivated_sound_played = False  # Reset spike sound flag
            lever_data = self.game_map.lever_layer("levers")
            self.lever_objects = []
            for i, lever_info in enumerate(lever_data):
                lever_id = f"lever{i+1}"
                lever = Lever(lever_info['x'], lever_info['y'], lever_info['type'], lever_id=lever_id)
                self.lever_objects.append(lever)

    def spawn_enemy(self, x, y, enemy_type):
        data = enemy_data[enemy_type]
        enemy = Enemy(x, y, enemy_type, data)
        self.enemies.append(enemy)
       
    def load_enemies_for_level(self, enemies_list):
        level_key = f"level{self.level}"
        for enemy_type, data in enemy_data.items():
            if "spawn_locations" in data and level_key in data["spawn_locations"]:
                for spawn_point in data["spawn_locations"][level_key]:
                    enemy = Enemy(spawn_point["x"], spawn_point["y"], enemy_type,data)
                    enemies_list.append(enemy)
                    print(f"Spawned {enemy_type} at ({spawn_point['x']}, {spawn_point['y']})")

        #for i in range(2): 
        #    enemy_type = "chort"
         #   data = enemy_data[enemy_type]
        #    enemies.append(Enemy(player_x + (50 * i), player_y + (50 * i), enemy_type))
        
    def make_path_grid(self):
        walkable_tiles = []
        enemy_width_tiles = 2  
        enemy_height_tiles = 2  

        for y in range(self.game_map.tmx_data.height):
            row = []
            for x in range(self.game_map.tmx_data.width):
                blocked = False

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

    def player_damage(self, damage_amount):
        if self.player_damage_cooldown <= 0:
            self.health_bar.damage(damage_amount)
            self.player_sounds["hurt"].play()
            self.player_damage_cooldown = self.player_damage_cooldown_duration

    def restart_game(self):
        self.level = 1
        self.game_over = False
        self.death_sound_played = False
        
        self.health_bar.life = 100
        self.health_bar.update(100)
        self.player_damage_cooldown = 0
        self.music.play_level_music(1)
        
        self.game_map = TiledMap("Tiled/level1.tmx")
        self.game_map.set_current_level(self.level)
        self.path_grid = self.make_path_grid()
        
        self.level2 = level2()
        self.levers = {1: False, 2: False, 3: False, 4: False} 
        self.game_map.set_all_levers_pulled(False) 
        self.spikes_deactivated_sound_played = False 
        
        player_x = self.game_map.width // 2
        player_y = self.game_map.height // 2
        self.player.x = player_x
        self.player.y = player_y
        
        self.enemies.clear()
        self.particles.clear()
        
        self.load_enemies_for_level(self.enemies)
        
        self.camera.zoom = 10
        self.camera.update(self.player)
        
        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)
        self.camera.zoom = 10
        self.camera.update(self.player)

        self.health_bar.update(self.health_bar.life)

        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)



