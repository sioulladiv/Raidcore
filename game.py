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
from ui.experience import ExperienceBar
from ui.game_over import GameOverScreen
from ui.music import Music
from ui.level_logic import level2
from world.lever import Lever
from utils.culling import FrustumCuller
from config.game_settings import game_settings

import json
import os
import random

with open("data/enemy_data.json", "r") as f:
    enemy_data = json.load(f)

with open("data/level_data.json", "r") as f:
    level_data = json.load(f)

tile_size = 16


class Game:
    FPS = 40

    def __init__(self, screen_width, screen_height, displaySize, zoom_level=1.0):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.displaySize = displaySize
        self.zoom_level = zoom_level
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.level = 1
        self.pling_sounds = []

        self.fps_text_font = pygame.font.SysFont("Verdana", 20)
        
        # Load all sound files from the Orbs folder, copies of original with small changes in pitch like in minecraft
        orbs_folder = "Assets/Sounds/Orbs"
        if os.path.exists(orbs_folder):
            for filename in os.listdir(orbs_folder):
                if filename.lower().endswith(('.mp3', '.wav', '.ogg')):
                    try:
                        sound_path = os.path.join(orbs_folder, filename)
                        sound = pygame.mixer.Sound(sound_path)
                        self.pling_sounds.append(sound)
                        #print(f"Loaded orb sound: {str(filename)}")
                    except pygame.error as e:
                        print(f"Failed to load {filename}: {e}")
        
        if not self.pling_sounds:
            try:
                self.pling_sounds.append(pygame.mixer.Sound("Assets/Sounds/orb.mp3"))
                print("Loaded default orb sound: orb.mp3")
            except pygame.error as e:
                print(f"Failed to load default orb sound: {e}")
        
        print(f"Total orb sounds loaded: {len(self.pling_sounds)}")
        pygame.display.set_caption("Dungeon Game")

        self.game_map = TiledMap("Tiled/level{}.tmx".format(self.level))
        self.game_map.set_current_level(self.level)

        self.camera = Camera(self.screen_width, self.screen_height, zoom_level)

        self.player = Player(100, 100, 32, 32, (0, 255, 0), self.displaySize)
        self.enemies = []
        self.bullets = []
        self.music = Music()
        self.light = Lighting(200)

        self.health_bar = HealthBar(int(20 * self.displaySize), int(30 * self.displaySize),
                        int(300 * self.displaySize), int(60 * self.displaySize), self.displaySize)

        self.experience_bar = ExperienceBar(int(20 * self.displaySize), int(130 * self.displaySize),
                        int(300 * self.displaySize), int(60 * self.displaySize), self.displaySize)
        self.player_damage_cooldown = 0
        self.player_damage_cooldown_duration = 60 
        self.xp = 0

        self.menu = BunkerMenu(self.screen_width // 2 - 150, self.screen_height // 2 - 150, self.displaySize)
        self.transition_timer = 0

        self.lightlevel = level_data["level1"]["lighting"]

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

        # set chest sounds for future use
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
        self.press_e_image = pygame.transform.scale(self.press_e_image, (240 * self.displaySize, 192 * self.displaySize))  
        self.show_press_e = False
        self.path_grid = self.make_path_grid()

        pygame.font.init()
        self.xp_font = pygame.font.Font(None, 36)

        #load all animations from letter_animation folder for letter opening animation on level 1 :)
        self.letter_frames = []
        letter_folder = "Assets/letter_animation"
        if os.path.exists(letter_folder):
            frame_files = sorted([f for f in os.listdir(letter_folder) if f.endswith('.png')])
            for frame_file in frame_files:
                # join folder path with file to get full path
                frame_path = os.path.join(letter_folder, frame_file)
                frame_image = pygame.image.load(frame_path)
                original_ratio = 240 / 180
                scale_x = self.screen_width / 240
                scale_y = self.screen_height / 180
                scale = min(scale_x, scale_y) * 0.8

                new_width = int(240 * scale)
                new_height = int(180 * scale)
                frame_image = pygame.transform.scale(frame_image, (new_width, new_height))
                self.letter_frames.append(frame_image)

        #settings all variables to properly time the animation
        self.show_letter = False
        self.letter_frame_index = 0
        self.letter_animation_timer = 0
        self.letter_animation_speed = 100  
        self.letter_animation_complete = False
        if self.letter_frames:
            self.letter_x = (self.screen_width - self.letter_frames[0].get_width()) // 2
            self.letter_y = (self.screen_height - self.letter_frames[0].get_height()) // 2
        else:
            self.letter_x = 100
            self.letter_y = 100

        #instantiate game over screen
        self.game_over_screen = GameOverScreen(self.screen_width, self.screen_height)
        self.game_over = False
        self.death_sound_played = False
        self.spikes_deactivated_sound_played = False  

        #fetch player starting position from level data json file
        self.player.x , self.player.y = level_data[f"level{self.level}"]["start_pos"]
        
    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Dungeon Escape")

        # settings frustrum culler for oprimisation especially for level 3 where there are many ennemies and 1000+ tiles to render at once
        # basically it only render tiles that are visible within the camera's view instead of rendering the whole surface every frame
        culler = FrustumCuller(self.screen_width, self.screen_height)
    
        health_bar = self.health_bar
        experience_bar = self.experience_bar
        health_bar.update(100)  
        experience_bar.update(0)
        light = Lighting(350)
        
        
        collision_tiles, spike_tiles = self.reload_collision_data()

        endlevel_tiles = self.game_map.endlevel_layer("endlevel")

        gun = Gun(0, 0, "pistol", self.displaySize)
        player_x = self.game_map.width // 2
        player_y = self.game_map.height // 2
        self.player = Player(player_x, player_y, 16, 28, (255, 0, 0), self.displaySize)
    
        self.load_enemies_for_level(self.enemies)

        zoom_level = 13*self.displaySize
        camera = Camera(self.screen_width, self.screen_height, zoom_level)
        clock = pygame.time.Clock()
        running = True
        self.particles = []
    
      
        self.map_needs_collision_update = False
        self.last_all_levers_pulled = False

        # get all chest info into self.chests
        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)
        #same for levers
        lever_data = self.game_map.lever_layer("levers")
        self.lever_objects = []  
        for i, lever_info in enumerate(lever_data):
            lever_id = f"lever{i+1}" 
            lever = Lever(lever_info['x'], lever_info['y'], lever_info['type'], lever_id=lever_id)
            self.lever_objects.append(lever)

    
        while running:
            # print(f"x: {self.player.x}, y: {self.player.y}")  # Only for debugging
            self.life = self.health_bar.life
            self.experience = self.experience_bar.experience

            #logic for game over for sound effects and music to terminate when player dead
            if self.life <= 0 and not self.game_over:
                self.game_over = True
                if not self.death_sound_played:
                    volume = 0.7 * game_settings.get_sfx_volume()
                    self.player_sounds["death"].set_volume(volume)
                    self.player_sounds["death"].play()
                    self.death_sound_played = True
                self.music.play_game_over_music()
            dt = clock.tick(self.FPS)
            
            if self.player_damage_cooldown > 0:
                self.player_damage_cooldown -= 1

            if not self.game_over:
                self.music.update(self.level)
            
            gun.update(camera, self.player, dt, collision_tiles) 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type >= pygame.USEREVENT + 1 and event.type <= pygame.USEREVENT + 10:
                    # Handle delayed XP pling sounds like in minecraft
                    sound_index = event.type - pygame.USEREVENT - 1
                    delayed_sound_attr = f'delayed_pling_{sound_index + 1}'
                    # play the stored pling sound when player gains xp
                    # it works by playing a random sound from the pling_sounds list and setting a delay

                    if hasattr(self, delayed_sound_attr):
                        # Play the stored sound
                        stored_sound = getattr(self, delayed_sound_attr)
                        stored_sound.play()
                        # Clean up the stored sound
                        delattr(self, delayed_sound_attr)
                    else:
                        # Fallback: select a random pling sound
                        if self.pling_sounds:
                            pling_sound = random.choice(self.pling_sounds)
                            base_volume = random.uniform(0.3, 0.8)
                            final_volume = base_volume * game_settings.get_sfx_volume()
                            pling_sound.set_volume(final_volume)
                            pling_sound.play()
                    
                    pygame.time.set_timer(event.type, 0)  # Disable this timer

                # Handle events for game over screen
                elif self.game_over:
                    result = self.game_over_screen.handle_events([event])
                    if result == "restart":
                        self.restart_game()
                    elif result == "quit":
                        running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        if self.level == 1:
                            # On level 1 there is a chest, if you get close enough a letter should popup when you press e
                            # This is the logic for showing the letter and playing the minecraft chest sound
                            if self.show_letter:
                                volume = 0.8 * game_settings.get_sfx_volume()
                                self.chest_sounds["close"].set_volume(volume)
                                self.chest_sounds["close"].play()
                                self.show_letter = False
                                self.letter_animation_complete = False
                                self.letter_frame_index = 0
                                self.letter_animation_timer = 0
                            elif self.show_press_e:
                                for chest in self.chests:
                                    if chest.is_near_player(self.player):
                                        self.show_letter = True
                                        volume = 0.8 * game_settings.get_sfx_volume()
                                        self.chest_sounds["open"].set_volume(volume)
                                        self.chest_sounds["open"].play()
                                        self.letter_frame_index = 0
                                        self.letter_animation_timer = 0
                                        self.letter_animation_complete = False
                                        break
                        elif self.level == 2:
                            # On level 2 the E key is used to interact with levers
                            if self.level2.all_levers_pulled:
                                break
                            else:
                                for i, lever in enumerate(self.lever_objects):
                                    # check if lever is near player
                                    if lever.is_near_player(self.player) and not lever.is_pulled:
                                        if lever.pull(): 
                                            # if lever is pulled increment lever_number and update lever state dict
                                            lever_number = i + 1
                                            self.levers[lever_number] = True
                                            lever_id = lever.lever_id or f"lever{lever_number}"
                                            # sound logic for lever
                                            if self.level2.pull_lever(lever_id):
                                                self.game_map.update_lever_state(lever_id, True)
                                                volume = 0.6 * game_settings.get_sfx_volume()
                                                self.lever_sound.set_volume(volume)
                                                self.lever_sound.play()  
                                                #print(f"Pulled {lever_id}")
                                        break

            self.player.update_animation(dt)
            health_bar.update_animation(dt) 

            keys = pygame.key.get_pressed()

            if not self.show_letter and not self.game_over:
                self.player.update(keys, collision_tiles, endlevel_tiles, self, spike_tiles)
                camera.update(self.player)
                light.update(self.player, camera, self.lightlevel)

                self.show_press_e = False
                
                if self.level == 1:
                    for chest in self.chests:
                        if chest.is_near_player(self.player):
                            # show the popup to press e to interact with the chest
                            self.show_press_e = True
                            break
                
                elif self.level == 2:
                    for lever in self.lever_objects:
                        if lever.is_near_player(self.player) and not lever.is_pulled:
                            # same as above but for the levers
                            self.show_press_e = True
                            break

                # update enemies every frame
                for enemy in list(self.enemies):
                    enemy.update(keys, collision_tiles, self.player, self.enemies, self.path_grid, gun.bullets, health_bar, self.particles, self)
                    enemy.update_animation(dt)
            # update fade overlay for just after level change.
            # Increase alpha value until it reaches 255
            if self.fade_overlay_active:
                self.fade_overlay_timer += dt
                progress = self.fade_overlay_timer / self.fade_overlay_duration
                if progress >= 1.0:
                    self.fade_overlay_active = False
                    self.fade_overlay_alpha = 0
                else:
                    self.fade_overlay_alpha = int(255 * (1 - progress))

            # update letter animation, changing frame
            if self.show_letter and not self.letter_animation_complete and len(self.letter_frames) > 0:
                self.letter_animation_timer += dt
                if self.letter_animation_timer >= self.letter_animation_speed:
                    self.letter_animation_timer = 0
                    self.letter_frame_index += 1
                    if self.letter_frame_index >= len(self.letter_frames):
                        self.letter_frame_index = len(self.letter_frames) - 1
                        self.letter_animation_complete = True

            # update every particle that was spawned when an enemy was killed
            for particle in list(self.particles):
                particle.update(dt)
                if particle.is_dead():
                    self.particles.remove(particle)
            
            # Calculate visible tile bounds for culling
            tile_size = self.game_map.tmx_data.tilewidth 
            visible_bounds = culler.get_visible_tile_bounds(camera, tile_size)
            
            # Render map with culling directly to screen instead of using map_surface
            screen.fill((0, 0, 0))  
            tiles_rendered = self.game_map.render_to_screen(screen, camera, visible_bounds)

            # Reset culling stats for this frame if debugging
            if culler.debug_enabled:
                culler.culled_count = 0
                culler.total_count = 0

            self.player.draw(screen, camera)

            # Cull and draw enemies
            visible_enemies = culler.filter_visible_entities(self.enemies, camera, margin=100)
            for enemy in visible_enemies:
                enemy.draw(screen, camera)

            # Cull and draw particles
            visible_particles = []
            for particle in self.particles:
                if culler.is_point_visible(particle.x, particle.y, camera, margin=50):
                    visible_particles.append(particle)
            
            for particle in visible_particles:
                particle.draw(screen, camera)

            light.draw(screen, camera)
            gun.draw(screen, camera, self.player, dt)

            health_bar.draw(screen)
            # Draw the experience bar
            self.experience_bar.draw(screen)

            # Draw XP display
            #xp_text = self.xp_font.render(f"XP: {self.xp}", True, (255, 255, 255))
            #screen.blit(xp_text, (10, 100))

            if self.show_press_e and not self.show_letter:
                prompt_x = self.screen_width - (1.5 * 240) * self.displaySize
                prompt_y = self.screen_height - (1.5 * 192) * self.displaySize
                screen.blit(self.press_e_image, (prompt_x, prompt_y))

            if self.show_letter and len(self.letter_frames) > 0:
                current_frame = self.letter_frames[self.letter_frame_index]
                screen.blit(current_frame, (self.letter_x, self.letter_y))

            if self.fade_overlay_active and self.fade_overlay_alpha > 0:
                fade_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                fade_surface.fill((0, 0, 0, self.fade_overlay_alpha))
                screen.blit(fade_surface, (0, 0))

            if self.game_over:
                self.game_over_screen.draw(screen,self.level)
            os.system("cls" if os.name == "nt" else "clear")
            print(self.FPS)
            self.show_fps(clock)
            pygame.display.flip()

            if self.level == 2:
                previous_all_levers_pulled = self.level2.all_levers_pulled
                self.level2.update()
                self.game_map.set_all_levers_pulled(self.level2.all_levers_pulled)
                
                # Check if lever state changed and update collisions if needed
                if previous_all_levers_pulled != self.level2.all_levers_pulled:
                    self.map_needs_collision_update = True
                
                if not previous_all_levers_pulled and self.level2.all_levers_pulled and not self.spikes_deactivated_sound_played:
                    volume = 0.7 * game_settings.get_sfx_volume()
                    self.spike_retract.set_volume(volume)
                    self.spike_retract.play()
                    self.spikes_deactivated_sound_played = True

            # Update collision tiles when map state changes
            if self.map_needs_collision_update:
                collision_tiles, spike_tiles = self.reload_collision_data()
                
                # For level 2, handle spike tiles based on lever state
                if self.level == 2 and hasattr(self, 'level2') and self.level2.all_levers_pulled:
                    spike_tiles = []
                    #print("All levers pulled")
                
                # Update pathfinding grid when collision state changes
                self.path_grid = self.make_path_grid()
                    
                self.map_needs_collision_update = False
                endlevel_tiles = self.game_map.endlevel_layer("endlevel")
                endlevel_tiles = self.game_map.endlevel_layer("endlevel")


        #os.system("cls" if os.name == "nt" else "clear")#
            
        pygame.quit()


    def show_fps(self, clock):
        print(f"FPS: {clock.get_fps()}")
        text = self.fps_text_font.render(str(round(clock.get_fps(),2)), True, (255,255,255))
        self.screen.blit(text, (self.screen_width - 100, 50))

    def next_level(self):
        self.enemies.clear()
        self.particles.clear()
        self.player.x , self.player.y = level_data[f"level{self.level}"]["start_pos"]

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
            dt = clock.tick(self.FPS) 
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

        self.player.x , self.player.y = level_data[f"level{self.level}"]["start_pos"]

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

        # IMPORTANT: Reload collision tiles for the new level
        self.map_needs_collision_update = True

        if self.level == 2:
            self.level2 = level2()
            self.levers = {1: False, 2: False, 3: False, 4: False}  
            self.game_map.set_all_levers_pulled(False)  
            self.spikes_deactivated_sound_played = False  
            lever_data = self.game_map.lever_layer("levers")
            self.lever_objects = []
            for i, lever_info in enumerate(lever_data):
                lever_id = f"lever{i+1}"
                lever = Lever(lever_info['x'], lever_info['y'], lever_info['type'], lever_id=lever_id)
                self.lever_objects.append(lever)

        self.lightlevel = level_data[f"level{self.level}"]["lighting"]

    def reload_collision_data(self):
        """Reload collision data for the current level"""
        try:
            collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining 2"])
            spike_tiles = self.game_map.collision_layer(["spikes"])
            return collision_tiles, spike_tiles
        except Exception as e:
            try:
                collision_tiles = self.game_map.collision_layer(["wall lining", "wall lining2"])
                spike_tiles = self.game_map.collision_layer(["spikes"])
                return collision_tiles, spike_tiles
            except Exception as e2:
                try:
                    collision_tiles = self.game_map.collision_layer(["walllining1", "walllining2"])
                    spike_tiles = self.game_map.collision_layer(["spikes"])
                    return collision_tiles, spike_tiles
                except Exception as e3:
                    collision_tiles = self.game_map.collision_layer(["wall lining"])
                    spike_tiles = []
                    return collision_tiles, spike_tiles

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

        #for i in range(2): 
        #    enemy_type = "chort"
         #   data = enemy_data[enemy_type]
        #    enemies.append(Enemy(player_x + (50 * i), player_y + (50 * i), enemy_type))
        
    def make_path_grid(self):
        walkable_tiles = []
        tile_size = 16
        
        # Calculate maximum enemy dimensions for pathfinding clearance
        max_enemy_width = 0
        max_enemy_height = 0
        
        for enemy_type, data in enemy_data.items():
            enemy_width_tiles = max(1, (data["width"] + tile_size - 1) // tile_size)  # Round up
            enemy_height_tiles = max(1, (data["height"] + tile_size - 1) // tile_size)  # Round up
            max_enemy_width = max(max_enemy_width, enemy_width_tiles)
            max_enemy_height = max(max_enemy_height, enemy_height_tiles)
        
        print(f"Pathfinding using clearance: {max_enemy_width}x{max_enemy_height} tiles")
        
        # Get current collision tiles from the same method that works for player/enemy collision
        collision_tiles, spike_tiles = self.reload_collision_data()
        
        # For level 2, handle spike tiles based on lever state
        if self.level == 2 and hasattr(self, 'level2') and self.level2.all_levers_pulled:
            spike_tiles = []
        
        # Combine all obstacle tiles
        all_obstacle_tiles = collision_tiles + spike_tiles
        
        # Create a set of blocked tile coordinates for fast lookup
        blocked_tiles = set()
        for tile_rect in all_obstacle_tiles:
            # Convert pixel coordinates to tile coordinates
            tile_x = tile_rect.x // tile_size
            tile_y = tile_rect.y // tile_size
            blocked_tiles.add((tile_x, tile_y))
        
        # Generate pathfinding grid
        for y in range(self.game_map.tmx_data.height):
            row = []
            for x in range(self.game_map.tmx_data.width):
                # Check if this tile or adjacent tiles (for enemy size) are blocked
                blocked = False
                
                # Check if any tile within the largest enemy's footprint is blocked
                for check_y in range(y, min(self.game_map.tmx_data.height, y + max_enemy_height)):
                    for check_x in range(x, min(self.game_map.tmx_data.width, x + max_enemy_width)):
                        if (check_x, check_y) in blocked_tiles:
                            blocked = True
                            break
                    if blocked:
                        break
                
                # 1 = walkable, 0 = blocked (pathfinding library expects this format)
                row.append(1 if not blocked else 0)
            walkable_tiles.append(row)
        
        return walkable_tiles

    def player_damage(self, damage_amount):
        if self.player_damage_cooldown <= 0:
            self.health_bar.damage(damage_amount)
            volume = 0.6 * game_settings.get_sfx_volume()
            self.player_sounds["hurt"].set_volume(volume)
            self.player_sounds["hurt"].play()
            self.player_damage_cooldown = self.player_damage_cooldown_duration

    def collect_xp(self, xp_amount):
        """Collect XP when an enemy is killed"""
        self.xp += xp_amount
        
        # Play multiple pling sounds based on XP amount
        num_sounds = max(1, xp_amount // 2)  # At least 1 sound, then 1 per 2 XP
        
        for i in range(num_sounds):
            # Randomly select a pling sound from the array
            if self.pling_sounds:
                pling_sound = random.choice(self.pling_sounds)
                
                # Random volume variation (0.3 to 0.8 base, then apply settings)
                base_volume = random.uniform(0.3, 0.8)
                final_volume = base_volume * game_settings.get_sfx_volume()
                pling_sound.set_volume(final_volume)
                
                # Play with small delays between sounds for a cascade effect
                if i == 0:
                    pling_sound.play()
                else:
                    # Store the sound in a way that the timer can access it
                    setattr(self, f'delayed_pling_{i}', pling_sound)
                    pygame.time.set_timer(pygame.USEREVENT + 1 + i, i * 70)  # 70ms between each sound
        self.experience_bar.update(self.xp)
    def restart_game(self):
        # Reset level and game state
        self.level = 1
        self.game_over = False
        self.death_sound_played = False
        self.spikes_deactivated_sound_played = False
        
        # Reset health and player damage cooldown
        self.health_bar.life = 100
        self.health_bar.update(100)
        self.player_damage_cooldown = 0
        
        # Reset XP
        self.xp = 0
        
        # Reset music
        self.music.play_level_music(1)
        
        # Reload level 1 map
        self.game_map = TiledMap("Tiled/level1.tmx")
        self.game_map.set_current_level(self.level)
        self.path_grid = self.make_path_grid()
        
        # Reset level 2 state and levers
        self.level2 = level2()
        self.levers = {1: False, 2: False, 3: False, 4: False} 
        self.game_map.set_all_levers_pulled(False)
        self.lever_objects = []  # Clear lever objects
        
        # Reset player position
        self.player.x, self.player.y = level_data[f"level{self.level}"]["start_pos"]
        
        # Clear all dynamic objects
        self.enemies.clear()
        self.particles.clear()
        self.bullets.clear()  # Clear bullets
        
        # Reload enemies for level 1
        self.load_enemies_for_level(self.enemies)
        
        # Reset camera
        self.camera.zoom = 10
        self.camera.update(self.player)
        
        # Reset chests for level 1
        chest_data = self.game_map.chests_layer("chests")
        self.chests = []
        for chest_info in chest_data:
            chest = Chest(chest_info['x'], chest_info['y'], chest_info['type'])
            self.chests.append(chest)
        
        # Reset animation states
        self.show_letter = False
        self.letter_animation_complete = False
        self.letter_frame_index = 0
        self.letter_animation_timer = 0
        self.show_press_e = False
        
        # Reset fade overlay
        self.fade_overlay_alpha = 0
        self.fade_overlay_timer = 0
        self.fade_overlay_active = False
        
        # Reset lighting level
        self.lightlevel = level_data["level1"]["lighting"]
        
        # Force collision data reload
        self.map_needs_collision_update = True
        
        # Reset gun state (will be recreated in run method)
        # This ensures the gun doesn't carry over bullets or state from previous game