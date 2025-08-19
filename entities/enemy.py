import random
import pygame
from entities.particle import Particle
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement
from config.game_settings import game_settings

tile_size = 16

class Enemy:
    def __init__(self, x, y, Ennemytype='chort', data=None):
        pygame.mixer.init()
        self.x = x
        self.y = y
        self.width = data["width"]
        self.height = data["height"]
        self.speed = data["speed"] * random.uniform(0.8, 1.2) * 0.5 
        self.og_speed = self.speed
        self.lives = data["lives"]
        self.damage = data["damage"]
        self.color = (255, 0, 0)
        self.hit_timer = 0
        self.type = Ennemytype
        self.detection_range = data["detection_range"]
        self.path_find_timer = 0
        self.path_arr_index = 0
        self.collision_slowdown_timer = 0
        self.original_speed = self.speed
        self.particle_num = 10
        
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.max_velocity = self.speed
        self.acceleration = 0.3
        self.friction = 0.8
        
        self.smooth_x = float(x)
        self.smooth_y = float(y)

        self.sound_timer = random.uniform(0,200)

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = data["animations"]["idle"]["frames"] * 20
        self.is_moving = False
        self.facing_dir = 0
        self.collision_width = int(self.width * 0.7)
        self.collision_height = int(self.height * 0.6)
        self.collision_offset_x = (self.width - self.collision_width) // 2
        self.collision_offset_y = self.height - self.collision_height - 2
        self.colour = data["colour"]

    
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

        self.last_player_x = 0
        self.last_player_y = 0
        self.player_moved_threshold = 32  
        self.direct_movement_distance = 30 

        self.sounds = data["sound"]
        self.sound_objects = {}
        
        for sound_name, sound_file in self.sounds.items():
            if isinstance(sound_file, list):
                # Load all sounds in the list
                sound_list = []
                for sound_path in sound_file:
                    if sound_path:
                        try:
                            sound = pygame.mixer.Sound(sound_path)
                            sound.set_volume(random.uniform(0.4, 0.7))
                            sound_list.append(sound)
                        except pygame.error:
                            print(f"Warning: Could not load sound file {sound_path}")
                self.sound_objects[sound_name] = sound_list if sound_list else None
            else:
                # Single sound file
                if sound_file:
                    try:
                        sound = pygame.mixer.Sound(sound_file)
                        sound.set_volume(random.uniform(0.4, 0.7))
                        self.sound_objects[sound_name] = [sound]
                    except pygame.error:
                        print(f"Warning: Could not load sound file {sound_file}")
                        self.sound_objects[sound_name] = None

    def get_rect(self, x, y):
        return pygame.Rect(
            x + self.collision_offset_x,
            y + self.collision_offset_y,
            self.collision_width,
            self.collision_height
        )

    def get_distance_to_player(self, player):
        return ((player.x - self.x) ** 2 + (player.y - self.y) ** 2) ** 0.5

    def update(self, keys, tiles, player, enemies, collision_grid, bullets=None, health_bar=None, particles=None): 
        self.path_find_timer += 1
        distance_to_player = self.get_distance_to_player(player)

        if hasattr(self, 'collision_slowdown_timer') and self.collision_slowdown_timer > 0:
            self.collision_slowdown_timer -= 1
            if self.collision_slowdown_timer <= 0:
                self.speed = self.original_speed

        if not hasattr(self, 'path') or self.path is None:
            self.path = []
            self.path_arr_index = 0

        desired_velocity_x = 0.0
        desired_velocity_y = 0.0
        
        if distance_to_player < self.detection_range:
            player_moved_distance = ((player.x - self.last_player_x) ** 2 + (player.y - self.last_player_y) ** 2) ** 0.5
            
            should_update_path = (
                self.path_find_timer % 20 == 0 or  
                player_moved_distance > self.player_moved_threshold or  
                not self.path or len(self.path) == 0  
            )
            
            if should_update_path:
                self.update_pathfinding(player, collision_grid)
                self.last_player_x = player.x
                self.last_player_y = player.y
            
            if distance_to_player < self.direct_movement_distance:
                direction_x = (player.x + player.width // 2) - (self.x + self.width // 2)
                direction_y = (player.y + player.height // 2) - (self.y + self.height // 2)
                distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5
                
                # Don't move if too close to player (attack range)
                if distance_to_target > 20:  # Minimum attack distance
                    if distance_to_target > 0:
                        desired_velocity_x = (direction_x / distance_to_target) * self.max_velocity
                        desired_velocity_y = (direction_y / distance_to_target) * self.max_velocity
            else:
                if hasattr(self, 'path') and self.path and len(self.path) > 0:
                    if self.path_arr_index >= len(self.path):
                        self.path_arr_index = len(self.path) - 1
                    
                    if self.path_arr_index < len(self.path):
                        tile_x, tile_y = self.path[self.path_arr_index]
                        target_x = tile_x * tile_size + tile_size // 2
                        target_y = tile_y * tile_size + tile_size // 2

                        direction_x = target_x - (self.x + self.width // 2) 
                        direction_y = target_y - (self.y + self.height // 2)

                        if (direction_x) ** 2 + (direction_y) ** 2 < 18:  
                            self.path_arr_index += 1
                            if self.path_arr_index >= len(self.path):
                                direction_x = (player.x + player.width // 2) - (self.x + self.width // 2)
                                direction_y = (player.y + player.height // 2) - (self.y + self.height // 2)
                            else:
                                tile_x, tile_y = self.path[self.path_arr_index]
                                target_x = tile_x * tile_size + tile_size // 2
                                target_y = tile_y * tile_size + tile_size // 2
                                direction_x = target_x - (self.x + self.width // 2) 
                                direction_y = target_y - (self.y + self.height // 2)

                        distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5
                        if distance_to_target > 0:
                            desired_velocity_x = (direction_x / distance_to_target) * self.max_velocity
                            desired_velocity_y = (direction_y / distance_to_target) * self.max_velocity
                else:
                    direction_x = (player.x + player.width // 2) - (self.x + self.width // 2)
                    direction_y = (player.y + player.height // 2) - (self.y + self.height // 2)
                    distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5
                    if distance_to_target > 0:
                        desired_velocity_x = (direction_x / distance_to_target) * self.max_velocity * 0.7
                        desired_velocity_y = (direction_y / distance_to_target) * self.max_velocity * 0.7

        acceleration_factor = 0.7 if abs(desired_velocity_x) > 0 or abs(desired_velocity_y) > 0 else 0.5
        
        self.velocity_x += (desired_velocity_x - self.velocity_x) * acceleration_factor
        self.velocity_y += (desired_velocity_y - self.velocity_y) * acceleration_factor
        
        if abs(desired_velocity_x) < 0.1:
            self.velocity_x *= 0.85  
        if abs(desired_velocity_y) < 0.1:
            self.velocity_y *= 0.85

        speed_threshold = 0.05
        self.is_moving = abs(self.velocity_x) > speed_threshold or abs(self.velocity_y) > speed_threshold
        
        if abs(self.velocity_x) > speed_threshold:
            if self.velocity_x > 0:
                self.facing_dir = 1  
            else:
                self.facing_dir = 0

        # Play sounds based on movement state
        if self.is_moving:
            self.play_sound(player, "attack")
        else:
            self.play_sound(player, "idle")

        if bullets:
            enemy_rect = self.get_rect(self.x, self.y)
            for bullet in list(bullets):
                bullet_rect = bullet.get_rect()
                if enemy_rect.colliderect(bullet_rect) and bullet.alive:
                    self.lives -= bullet.damage
                    bullet.alive = False
                    self.hit_timer = 10
                    
                    if self.lives <= 0:
                        if self in enemies:
                            # Stop all currently playing sounds
                            for sound_name, sound_list in self.sound_objects.items():
                                if sound_list is not None:
                                    for sound in sound_list:
                                        if hasattr(sound, 'stop'):
                                            sound.stop()
                            self.play_sound(player, "death")
                            enemies.remove(self)
                            if particles is not None:
                                for i in range(self.particle_num): 
                                    particles.append(Particle(
                                        self.x + self.width // 2, 
                                        self.y + self.height // 2, 
                                        random.uniform(-5, 5),  
                                        random.uniform(-5, 5), 
                                        self.colour,
                                        random.randint(3, 5),  
                                        random.randint(30, 60),
                                    ))
                    else:
                        self.play_sound(player, "hurt")
                        return

        # Check enemy-player collision for damage (regardless of movement)
        enemy_rect = self.get_rect(self.x, self.y)
        if enemy_rect.colliderect(player.get_rect(player.x, player.y)):
            if health_bar:
                health_bar.damage(self.damage)

        # Decrement hit timer (for white hit effect)
        if self.hit_timer > 0:
            self.hit_timer -= 1

        if self.is_moving or abs(self.velocity_x) > 0.01 or abs(self.velocity_y) > 0.01:
            self.move_and_collide(self.velocity_x, self.velocity_y, tiles, enemies, bullets, player, health_bar, particles)

    def update_pathfinding(self, player, collision_grid):
        if not hasattr(self, 'path'):
            self.path = []
            self.path_arr_index = 0

        try:
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
                    self.path = [(node.x, node.y) for node in path[1:]]
                    self.path_arr_index = 0
        except Exception as e:
            print("Error occurred while updating pathfinding:", e)
            self.path = []
            self.path_arr_index = 0

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
            self.speed = self.og_speed
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

    def move_and_collide(self, dx, dy, tiles, enemies, bullets=None, player=None, health_bar=None, particles=None):
        self.x += dx
        enemy_rect = self.get_rect(self.x, self.y)
        
        for wall in tiles:
            if enemy_rect.colliderect(wall):
                if dx > 0:
                    self.x = wall.left - self.collision_width - self.collision_offset_x
                elif dx < 0:
                    self.x = wall.right - self.collision_offset_x
                break
        
        for other_enemy in enemies:
            if other_enemy != self:
                other_rect = other_enemy.get_rect(other_enemy.x, other_enemy.y)
                if enemy_rect.colliderect(other_rect):
                    if dx > 0:
                        self.x = other_rect.left - self.collision_width - self.collision_offset_x
                    elif dx < 0:
                        self.x = other_rect.right - self.collision_offset_x
                    
                    self.collision_slowdown_timer = 30
                    self.speed = self.original_speed * 0.3
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
        
        for other_enemy in enemies:
            if other_enemy != self:
                other_rect = other_enemy.get_rect(other_enemy.x, other_enemy.y)
                if enemy_rect.colliderect(other_rect):
                    if dy > 0:
                        self.y = other_rect.top - self.collision_height - self.collision_offset_y
                    elif dy < 0:
                        self.y = other_rect.bottom - self.collision_offset_y
                    
                    self.collision_slowdown_timer = 30
                    self.speed = self.original_speed * 0.3
                    break

    def play_sound(self, player, type="attack"):
        distance = self.get_distance_to_player(player)
        
        if type == "attack":
            # Only play attack sounds when close to player and timer allows
            if distance < 60 and self.sound_timer <= 0:
                if type in self.sound_objects and self.sound_objects[type] is not None:
                    sound_list = self.sound_objects[type]
                    if sound_list:
                        sound = random.choice(sound_list)
                        base_volume = max(0, 1 - distance/50)
                        final_volume = base_volume * game_settings.get_sfx_volume()
                        sound.set_volume(final_volume)
                        sound.play()
                    # Set longer timer to prevent rapid repeating (2-4 seconds)
                    self.sound_timer = random.uniform(80, 160)
        elif type == "idle":
            # Play idle sounds when not moving and timer allows
            if not self.is_moving and distance < 100 and self.sound_timer <= 0:
                if type in self.sound_objects and self.sound_objects[type] is not None:
                    sound_list = self.sound_objects[type]
                    if sound_list:
                        sound = random.choice(sound_list)
                        base_volume = max(0, 1 - distance/100)
                        final_volume = base_volume * game_settings.get_sfx_volume()
                        sound.set_volume(final_volume)
                        sound.play()
                    # Set longer timer for idle sounds (4-8 seconds)
                    self.sound_timer = random.uniform(160, 320)
        else:
            # Play other sounds (hurt/death) immediately
            if type in self.sound_objects and self.sound_objects[type] is not None:
                sound_list = self.sound_objects[type]
                if sound_list:
                    sound = random.choice(sound_list)
                    base_volume = max(0, 1 - distance/200)
                    final_volume = base_volume * game_settings.get_sfx_volume()
                    sound.set_volume(final_volume)
                    sound.play()
        
        # Decrement timer
        if self.sound_timer > 0:
            self.sound_timer -= 1
