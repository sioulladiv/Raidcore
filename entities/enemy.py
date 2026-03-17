"""Enemy entity: AI movement, pathfinding, combat and animation."""
from __future__ import annotations

import random
import pygame
from typing import TYPE_CHECKING
from entities.particle import Particle
from utils.pathfinding import Pathfind
from config.game_settings import game_settings
import os

if TYPE_CHECKING:
    from entities.player import Player
    from world.camera import Camera
    from ui.health_bar import HealthBar
    from game import Game

tile_size = 16


class Enemy:
    """An enemy character with autonomous AI behaviour.

    Movement is driven by an A* pathfinder when the player is within detection
    range.  The enemy resolves collisions with walls and other enemies and
    inflicts/receives damage through bullet or knife hit-testing each frame.
    """
    def __init__(self, x: float, y: float, Ennemytype: str = 'chort', data: dict | None = None) -> None:
        """Create an enemy from its JSON data dictionary.

        Args:
            x: World x spawn coordinate.
            y: World y spawn coordinate.
            Ennemytype: String key matching an entry in ``enemy_data.json``
                (e.g. ``'chort'``, ``'goblin'``).
            data: Parsed dictionary from ``enemy_data.json`` for this enemy
                type.  Must contain at least ``width``, ``height``,
                ``speed``, ``lives``, ``damage``, ``detection_range``,
                ``animations``, ``frame_path``, ``colour`` and ``sound``.
        """
        self.x = x
        self.y = y
        self.width = data["width"]
        self.height = data["height"]

        # Randomize speed slightly for natural variation between enemies of the same type
        #so they don't all move in perfect unison
        self.speed = data["speed"] * random.uniform(0.8, 1.2) * 0.5 
        self.og_speed = self.speed
        self.lives = data["lives"]
        self.damage = data["damage"]
        self.color = (255, 0, 0)
        self.hit_timer = 0
        self.type = Ennemytype
        self.detection_range = data["detection_range"]
        
        self.xp_reward = data.get("xp")
        
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


        # Load animation frames based on provided data
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


        # get frames for animation when idel from json file
        self.idle_frames = []
        for i in range(data["animations"]["idle"]["frames"]):
            img = pygame.image.load(f"{data['frame_path']}_idle_anim_f{i}.png")
            img = pygame.transform.scale(img, (self.width, self.height))
            self.idle_frames.append(img)

        # Get frames for animation when moving running or walking from json file
        self.walk_frames = []
        for i in range(data["animations"]["run"]["frames"]):
            img = pygame.image.load(f"{data['frame_path']}_run_anim_f{i}.png")
            img = pygame.transform.scale(img, (self.width, self.height))
            self.walk_frames.append(img)

        self.last_player_x = 0
        self.last_player_y = 0
        self.player_moved_threshold = 32  
        self.direct_movement_distance = 10 

        # Load sounds based on provided data
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
                            print(f"could not load sound file{sound_path}")
                self.sound_objects[sound_name] = sound_list if sound_list else None
            else:
                # Single sound file
                if sound_file:
                    try:
                        sound = pygame.mixer.Sound(sound_file)
                        sound.set_volume(random.uniform(0.4, 0.7))
                        self.sound_objects[sound_name] = [sound]
                    except pygame.error:
                        print(f"could not load sound file{sound_file}")
                        self.sound_objects[sound_name] = None

    def cleanup(self) -> None:
        """Clean up resources when enemy is removed"""
        #prevents memory leaks which I have had issues with before
        # Stop any playing sounds
        for sound_name, sound_list in self.sound_objects.items():
            if isinstance(sound_list, list):

                for sound in sound_list:
                    if sound:
                        sound.stop()
            elif sound_list: sound_list.stop()
        
        # Clear references
        self.sound_objects.clear()
        self.idle_frames.clear()

        self.walk_frames.clear()
    
    def get_rect(self, x: float, y: float) -> pygame.Rect:
        """Return the enemy's collision rectangle at position (x, y).

        Args:
            x: World x-coordinate to use.
            y: World y-coordinate to use.

        Returns:
            ``pygame.Rect`` for the enemy's collision bounds.
        """
        #return pygame rect of enemy
        return pygame.Rect(
            x + self.collision_offset_x,
            y + self.collision_offset_y,
            self.collision_width,
            self.collision_height
        )

    def get_distance_to_player(self, player: Player) -> float:
        """Return the Euclidean distance from this enemy to the player.

        Args:
            player: The player entity.

        Returns:
            Distance in world pixels.
        """
        return ((player.x - self.x) ** 2 + (player.y - self.y) ** 2) ** 0.5

    def update(
self,
keys: pygame.key.ScancodeWrapper,
tiles: list[pygame.Rect],
player: Player,
enemies: list[Enemy],
collision_grid: list[list[int]],
bullets: list | None = None,
health_bar: HealthBar | None = None,
particles: list | None = None,
game: Game | None = None,
knife_attack: pygame.Rect | None = None,
knife_damage: float = 0,
    ) -> None:
        """Run one frame of enemy AI, collision and combat logic.

        Args:
            keys: Current keyboard state (unused by enemy but kept for
                signature parity).
            tiles: Wall collision rectangles for AABB(Axis-Aligned Bounding Box collision handling) resolution.
            player: The player entity.
            enemies: List of all active enemies (used for enemy–enemy push).
            collision_grid: 2-D grid where 1 = walkable, 0 = blocked,
                used by the pathfinder.
            bullets: Active bullet objects to test for hits.
            health_bar: Player's health bar; receives damage on contact.
            particles: Particle list to append death effects to.
            game: Game instance for XP collection callbacks.
            knife_attack: Hitbox rect of an active knife swing, or ``None``.
            knife_damage: Damage dealt by a knife swing (0 when not attacking).
        """
        self.path_find_timer += 1
        distance_to_player = self.get_distance_to_player(player)

        if hasattr(self, 'collision_slowdown_timer') and self.collision_slowdown_timer  > 0:
            self.collision_slowdown_timer -= 1
            if self.collision_slowdown_timer <= 0:
                self.speed = self.original_speed

        if not hasattr(self, 'path') or self.path is None:
            self.path = []
            self.path_arr_index = 0

        desired_velocity_x = 0.0
        desired_velocity_y = 0.0
        if distance_to_player < self.detection_range:
            player_moved_distance = ((player.x - self.last_player_x)**2 + (player.y - self.last_player_y)**2)**0.5
            
            should_update_path = (
                #increase for more frequent pathfinding, decrease for less but more efficient pathfinding
                self.path_find_timer % 45 == 0 or 
                player_moved_distance > self.player_moved_threshold or  
                not self.path or len(self.path) == 0  
            )
            
            # Only pathfind if within detection range
            if should_update_path:
                self.update_pathfinding(player, collision_grid)
                self.last_player_x = player.x
                self.last_player_y = player.y
            
            if distance_to_player < self.direct_movement_distance and should_update_path:
                print("direct movement")
                direction_x = player.x  - self.x 
                direction_y = player.y - self.y
                distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5
                direction_x = (player.x + player.width // 2) - (self.x + self.width // 2)
                direction_y = (player.y + player.height // 2) - (self.y + self.height // 2)
                distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5
                if distance_to_target > 0:
                    desired_velocity_x = (direction_x / distance_to_target) * self.max_velocity * 0.7
                    desired_velocity_y = (direction_y / distance_to_target) * self.max_velocity * 0.7
                # Don't move if too close to player (attack range)
                # Removed debug prints for performance
                
            else:
                # Follow path if it exists and is valid
                if hasattr(self, 'path') and self.path and len(self.path) > 0:
                    # Removed debug prints for performance
                    if self.path_arr_index >= len(self.path):
                        self.path_arr_index = len(self.path) - 1
                    
                    # If we've reached the current target tile, move to the next one
                    if self.path_arr_index < len(self.path):
                        tile_x, tile_y = self.path[self.path_arr_index]
                        target_x = tile_x * tile_size + tile_size // 2
                        target_y = tile_y * tile_size + tile_size // 2
                        #calculate direction vector towards current target tile
                        direction_x = target_x - (self.x + self.width // 2) 
                        direction_y = target_y - (self.y + self.height // 2)

                        #if close enough to the target tilethen switch to the next one in the path
                        if (direction_x) *2 + (direction_y)**2 < 18: 
                            #as shown in design section values might be different in example 18 represents a bit more than one tile
                            self.path_arr_index += 1
                            if self.path_arr_index >= len(self.path):
                                direction_x = (player.x + player.width // 2) - (self.x + self.width // 2)
                                direction_y = (player.y + player.height // 2) - (self.y + self.height // 2)
                            else:
                                #calculate direction towards next tile in path
                                tile_x, tile_y = self.path[self.path_arr_index]
                                target_x = tile_x*tile_size + tile_size //2
                                target_y = tile_y* tile_size +tile_size //2
                                direction_x = target_x - (self.x + self.width // 2) 
                                direction_y = target_y - (self.y + self.height // 2)

                        #normalise direction and scale by speed to get desired velocity
                        distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5
                        if distance_to_target > 0:

                            desired_velocity_x = (direction_x / distance_to_target) * self.max_velocity
                            desired_velocity_y = (direction_y / distance_to_target) * self.max_velocity
                else:
                    # No path found or path is empty, so do direct movement towards player as fallback
                    direction_x = (player.x + player.width // 2) - (self.x + self.width // 2)
                    direction_y = (player.y + player.height // 2) - (self.y + self.height // 2)
                    distance_to_target = (direction_x ** 2 + direction_y ** 2) ** 0.5
                    if distance_to_target > 0:
                        desired_velocity_x = (direction_x / distance_to_target) * self.max_velocity * 0.7
                        desired_velocity_y = (direction_y / distance_to_target) * self.max_velocity * 0.7

        # enemy movement is not natural enough
        # so use acceleration to smoothly change velocity towards desired velocity, and friction to slow down when no input

        if abs(desired_velocity_x) > 0 or abs(desired_velocity_y) > 0 : acceleration_factor = 0.7
        else: acceleration_factor  = 0.5

        # Smoothly adjust velocity towards desired velocity        
        self.velocity_x += (desired_velocity_x - self.velocity_x)*acceleration_factor
        self.velocity_y += (desired_velocity_y - self.velocity_y)*acceleration_factor
        
        if abs(desired_velocity_x) < 0.1: self.velocity_x *= 0.85  
        if abs(desired_velocity_y) < 0.1: self.velocity_y *= 0.85

        #determine if the enemy is moving based on velocity magnitude with a small threshold to prevent jitter when nearly stationary
        speed_threshold = 0.05
        self.is_moving = abs(self.velocity_x) > speed_threshold or abs(self.velocity_y) > speed_threshold
        
        if abs(self.velocity_x) > speed_threshold:
            if self.velocity_x > 0: self.facing_dir = 1  
            else: self.facing_dir = 0

        # Idle ambient sound while stationary near player
        if not self.is_moving: self.play_sound(player, "idle")

        # Check knife attack collision
        if knife_attack and knife_damage > 0:
            enemy_rect = self.get_rect(self.x, self.y)
            if enemy_rect.colliderect(knife_attack):
                self.lives -= knife_damage
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
                        
                        # Collect XP before removing enemy
                        if game is not None and hasattr(self, 'xp_reward'):
                            game.collect_xp(self.xp_reward)
                        
                        # Remove enemy and spawn particles
                        enemies.remove(self)
                        if particles is not None:
                            for i in range(self.particle_num): 
                                particles.append(Particle(
                                    self.x + self.width // 2, 
                                    self.y + self.height // 2, 
                                    random.uniform(-1, 1),  
                                    random.uniform(-1, 1), 
                                    self.colour,
                                    random.randint(3, 5),  
                                    random.randint(30, 60),
                                ))
        
        # Check bullet collision
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
                            
                            # Collect XP before removing enemy
                            if game is not None and hasattr(self, 'xp_reward'):
                                game.collect_xp(self.xp_reward)
                            
                            enemies.remove(self)
                            if particles is not None:
                                for i in range(self.particle_num): 
                                    particles.append(Particle(
                                        self.x + self.width // 2, 
                                        self.y + self.height // 2, 
                                        random.uniform(-1, 1),  
                                        random.uniform(-1, 1), 
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
            self.play_sound(player, "attack")

        # Decrement hit timer (for white hit effect)
        if self.hit_timer > 0:
            self.hit_timer -= 1

        if self.is_moving or abs(self.velocity_x) > 0.01 or abs(self.velocity_y) > 0.01:
            self.move_and_collide(self.velocity_x, self.velocity_y, tiles, enemies, bullets, player, health_bar, particles)

    def update_pathfinding(self, player: Player, collision_grid: list[list[int]]) -> None:
        """Recompute the A* path from this enemy to the player.

        Results are stored in ``self.path`` as a list of ``(col, row)`` tile
        coordinates.  Does nothing if the start/goal tile is out of bounds.

        Args:
            player: The player entity providing the goal position.
            collision_grid: 2-D grid used by :class:`~utils.pathfinding.Pathfind`.
        """
        if not hasattr(self, 'path'):
            self.path = []
            self.path_arr_index = 0

        try:
            # Calculate start and end tile coordinates based on enemy and player positions
            start_x = int((self.x +self.width// 2) //16)
            start_y = int((self.y + self.height//2)// 16)

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
                # Use custom pathfinding - note: Pathfind uses (row, col) format
                pathfinder = Pathfind(collision_grid)
                # Start and goal are (row, col) = (y, x) in the grid
                path = pathfinder.find_path((start_y, start_x), (end_y, end_x))
                if path and len(path) > 1:
                    # Convert from (row, col) to (x, y) format, skip the first node (current position)
                    self.path = [(col, row) for row, col in path[1:]]
                    self.path_arr_index = 0

        except Exception as e:
            print("Error occurred while updating pathfinding:", e)
            self.path = []
            self.path_arr_index = 0

    def update_animation(self, dt: float) -> None:
        """Advance the sprite animation timer and flip to the next frame.
        Args:
            dt: Delta time in milliseconds since the last frame.
        """
        self.animation_timer += dt
        
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            
            # Pre-cache frame counts for better performance
            if self.is_moving:
                frame_count = len(self.walk_frames)
                if frame_count > 0:
                    self.current_frame = (self.current_frame + 1) % frame_count
            else:
                frame_count = len(self.idle_frames)
                if frame_count > 0:
                    self.current_frame = (self.current_frame + 1) % frame_count

    def draw(self, surface: pygame.Surface, camera: Camera | None = None) -> None:
        """Render the enemy sprite to *surface*, flashing white when hit.

        Args:
            surface: Pygame surface to draw onto.
            camera: Optional camera for world–to–screen transformation.
        """
        #select the correct animation frame based on movement state and facing direction
        if self.is_moving:
            current_img = self.walk_frames[self.current_frame % len(self.walk_frames)]
        else:
            current_img = self.idle_frames[self.current_frame % len(self.idle_frames)]

        if self.facing_dir == 0:
            current_img = pygame.transform.flip(current_img, True, False)

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

    def move_and_collide(
        self,
        dx: float,
        dy: float,
        tiles: list[pygame.Rect],
        enemies: list[Enemy],
        bullets: list | None = None,
        player: Player | None = None,
        health_bar: HealthBar | None = None,
        particles: list | None = None,
    ) -> None:
        """Move the enemy by (dx, dy) and resolve wall / enemy collisions.

        Axes are processed separately so the enemy slides along walls.  When
        two enemies overlap, the moving one is pushed back and slowed briefly.

        Args:
            dx: Horizontal movement this frame.
            dy: Vertical movement this frame.
            tiles: Wall collision rectangles.
            enemies: All active enemies (for push-apart resolution).
            bullets: Unused here but kept for signature consistency.
            player: Unused here but kept for signature consistency.
            health_bar: Unused here but kept for signature consistency.
            particles: Unused here but kept for signature consistency.
        """
        self.x += dx
        enemy_rect = self.get_rect(self.x, self.y)
        
        # Check collisions with walls and adjust position accordingly
        for wall in tiles:
            if enemy_rect.colliderect(wall):
                if dx > 0:
                    self.x = wall.left - self.collision_width - self.collision_offset_x
                elif dx < 0:
                    self.x = wall.right - self.collision_offset_x
                break
        
        # Check collisions with other enemies and push back if overlapping x-axis
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
        #same but y axis
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

    def play_sound(self, player: Player, type: str = "attack") -> None:
        """Attempt to play a distance-attenuated sound for this enemy.

        Args:
            player: The player entity (used to calculate distance).
            type: Sound category key, one of ``'attack'``, ``'idle'``,
                ``'hurt'``, or ``'death'``.
        """
        distance = self.get_distance_to_player(player)
        
        if type == "attack":
            # Play attack sounds when close to player and timer allows.
            # Keep attenuation range aligned with trigger distance to avoid
            # silent plays near the edge.
            max_distance = 80
            if distance < max_distance and self.sound_timer <= 0:
                if type in self.sound_objects and self.sound_objects[type] is not None:
                    sound_list = self.sound_objects[type]
                    if sound_list:
                        sound = random.choice(sound_list)
                        base_volume = max(0, 1 - distance / max_distance)
                        final_volume = base_volume * game_settings.get_sfx_volume()
                        sound.set_volume(final_volume)
                        sound.play()
                    self.sound_timer = random.uniform(80, 160)
        elif type == "idle":
            max_distance = 120
            if not self.is_moving and distance < max_distance and self.sound_timer <= 0:
                if type in self.sound_objects and self.sound_objects[type] is not None:
                    sound_list = self.sound_objects[type]
                    if sound_list:
                        sound = random.choice(sound_list)
                        base_volume = max(0, 1 - distance / max_distance)
                        final_volume = base_volume * game_settings.get_sfx_volume()
                        sound.set_volume(final_volume)
                        sound.play()
                    self.sound_timer = random.uniform(160, 320)
        else:
            #play hurt and death sounds without distance check but still with timer to prevent spam
            if type in self.sound_objects and self.sound_objects[type] is not None:
                sound_list = self.sound_objects[type]
                if sound_list:
                    sound = random.choice(sound_list)
                    base_volume = max(0, 1 - distance/200)
                    final_volume = base_volume * game_settings.get_sfx_volume()
                    sound.set_volume(final_volume)
                    sound.play()
        
        if self.sound_timer > 0:
            self.sound_timer -= 1