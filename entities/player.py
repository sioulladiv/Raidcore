"""Player entity: handles movement, animation and collision."""
from __future__ import annotations

import pygame
import os
from typing import TYPE_CHECKING
from config.game_settings import game_settings

if TYPE_CHECKING:
    from world.camera import Camera
    from game import Game

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Player:
    """The player character.

    Handles keyboard-driven movement, sprite animation, collision resolution
    against wall tiles and spike tiles, and sound playback.
    """
    def __init__(self, x: float, y: float, width: int, height: int, color: tuple[int, int, int], displaySize: float) -> None:
        """Create a Player instance and load sprites / sounds.

        Args:
            x: Initial world x-coordinate.
            y: Initial world y-coordinate.
            width: Sprite width in pixels.
            height: Sprite height in pixels.
            color: Fallback colour (RGB) used if sprites are unavailable.
            displaySize: Scaling ratio relative to the 2560×1440 reference
                resolution (screen_width / 2560).
        """
        self.x = x
        self.y = y
        self.speed = 1 
        self.color = (255, 0, 0)
        self.displaySize = displaySize

        self.width = width 
        self.height = height 

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 80 
        self.is_moving = False
        self.facing_dir = 0
        self.walking_sound_playing = False

        self.collision_width = int(width * 0.7)
        self.collision_height = int(height * 0.6)
        self.collision_offset_x = (width - self.collision_width) // 2
        self.collision_offset_y = height - self.collision_height - 2

        # Load sprites
        pygame.mixer.init()
        self.walking_sound = pygame.mixer.Sound("Assets/Sounds/Player/footsteps.mp3")
        self.idle_frames = []
        for i in range(21):
            img_path = os.path.join(project_root, "Dungeon", "frames", f"agent_idle{'0' + str(i) if i < 10 else str(i)}.png")
            img = pygame.image.load(img_path)
            img = pygame.transform.scale(img, (width, height))
            self.idle_frames.append(img)  
            self.idle_frames.append(img)  

        # Load walking frames (4 frames, looped)
        self.walk_frames = []
        for i in range(4):
            img_path = os.path.join(project_root, "Dungeon", "frames", f"agent_running{i}.png")
            img = pygame.image.load(img_path)
            img = pygame.transform.scale(img, (width, height))
            self.walk_frames.append(img)

    def update(self, keys: pygame.key.ScancodeWrapper, tiles: list[pygame.Rect], endlevel_tiles: list[pygame.Rect], game: Game, spike_tiles: list[pygame.Rect], dt: float = 16.67) -> None:
        """Update player position, handle input and check tile collisions.

        Args:
            keys: Current keyboard state returned by ``pygame.key.get_pressed()``.
            tiles: List of wall collision rectangles.
            endlevel_tiles: Rects that trigger a level transition on overlap.
            game: Game instance used to call ``next_level()`` and
                ``player_damage()``.
            spike_tiles: Rects of active spike traps.
            dt: Delta time in milliseconds (default 16.67 ≈ 60 FPS).
        """
        # Calculate delta time factor (normalized to 60 FPS)
        dt_factor = dt / 16.67  # 16.67ms = 1 frame at 60 FPS
        

        #debug when creating map and placing enemies
        # if keys[pygame.K_p]:
        #     print("Player position:", self.x, self.y)
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
        
        # Handle keyboard input for movement and actions
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

        # Handle walking sound playback
        if self.is_moving and not self.walking_sound_playing:
            volume = 0.3 * game_settings.get_sfx_volume()
            self.walking_sound.set_volume(volume)
            self.walking_sound.play(-1)
            self.walking_sound_playing = True
        elif not self.is_moving and self.walking_sound_playing:
            self.walking_sound.stop()
            self.walking_sound_playing = False

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        
        # Apply delta time factor for framerate independence
        #otherwise home pc runs much faster than school pc and makes testing difficult
        dx *= dt_factor

        dy *= dt_factor
        
        self.move_and_collide(dx, dy, tiles, game, spike_tiles)

        # Check for level transition
        for tile in endlevel_tiles:
            if self.get_rect(self.x, self.y).colliderect(tile):
                game.next_level()

    def move_and_collide(self, dx: float, dy: float, tiles: list[pygame.Rect], game: Game, spike_tiles: list[pygame.Rect]) -> None:
        """Move the player by (dx, dy) and resolve wall/spike collisions.

        Axes are processed separately so the player slides along walls rather
        than stopping dead.

        Args:
            dx: Horizontal movement this frame in pixels.
            dy: Vertical movement this frame in pixels.
            tiles: Wall collision rectangles.
            game: Game instance used to apply spike damage.
            spike_tiles: Active spike collision rectangles.
        """
        self.x += dx
        player_rect = self.get_rect(self.x, self.y)
        
        # Check horizontal collisions
        for wall in tiles:
            if player_rect.colliderect(wall):
                if dx > 0:  
                    self.x = wall.left - self.collision_width - self.collision_offset_x
                elif dx < 0:  
                    self.x = wall.right - self.collision_offset_x
                break
        
        # Check horizontal spike collisions
        if spike_tiles:
            player_rect = self.get_rect(self.x, self.y)
            for spike in spike_tiles:
                if player_rect.colliderect(spike):
                    game.player_damage(80)
                    if dx > 0: 
                        self.x = spike.left - self.collision_width - self.collision_offset_x
                    elif dx < 0: 
                        self.x = spike.right - self.collision_offset_x
                    break
        
        self.y += dy
        player_rect = self.get_rect(self.x, self.y)
        # Check vertical collisions
        for wall in tiles:
            if player_rect.colliderect(wall):
                if dy > 0:  
                    self.y = wall.top - self.collision_height - self.collision_offset_y
                elif dy < 0: 
                    self.y = wall.bottom - self.collision_offset_y
                break
        # Check vertical spike collisions
        if spike_tiles:
            player_rect = self.get_rect(self.x, self.y)
            for spike in spike_tiles:
                if player_rect.colliderect(spike):
                    game.player_damage(80)
                    if dy > 0: 
                        self.y = spike.top - self.collision_height - self.collision_offset_y
                    elif dy < 0:  
                        self.y = spike.bottom - self.collision_offset_y
                    break

    def get_rect(self, x: float, y: float) -> pygame.Rect:
        """Return the player's collision rectangle at position (x, y).

        The collision box is intentionally smaller than the sprite so the
        player can squeeze past tight gaps.

        Args:
            x: World x-coordinate to use for the calculation.
            y: World y-coordinate to use for the calculation.

        Returns:
            ``pygame.Rect`` representing the collision bounds.
        """
        return pygame.Rect(
            x + self.collision_offset_x,
            y + self.collision_offset_y,
            self.collision_width,
            self.collision_height
        )

    def update_animation(self, dt: float) -> None:
        """Advance the sprite animation timer and flip to the next frame.

        Args:
            dt: Delta time in milliseconds since the last frame.
        """
        self.animation_timer += dt
        
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            
            # Cache frame counts for better performance
            if self.is_moving:
                frame_count = len(self.walk_frames)
                if frame_count > 0:
                    self.current_frame = (self.current_frame + 1) % frame_count
            else:
                frame_count = len(self.idle_frames)
                if frame_count > 0:
                    self.current_frame = (self.current_frame + 1) % frame_count

    def draw(self, surface: pygame.Surface, camera: Camera | None = None) -> None:
        """Render the player sprite to *surface*.

        Args:
            surface: Pygame surface to draw onto.
            camera: Optional camera; when supplied the sprite is transformed
                to screen coordinates.  When ``None`` the world coordinates
                are used directly.
        """
        # Get current frame without redundant modulo
        if self.is_moving:
            frames = self.walk_frames
        else:
            frames = self.idle_frames
        
        if len(frames) == 0:
            return
        
        # Ensure current_frame is within bounds
        if self.current_frame >= len(frames):
            self.current_frame = 0
            
        current_img = frames[self.current_frame]
        
        # Apply horizontal flip if facing left
        if self.facing_dir == 0:
            current_img = pygame.transform.flip(current_img, True, False)
        
        # Position the sprite
        if camera:
            draw_x = self.x*camera.zoom+camera.offset_x
            draw_y = self.y*camera.zoom+camera.offset_y
            scaled_img = pygame.transform.scale(
                current_img, 
                (int(self.width *camera.zoom),int(self.height   * camera.zoom))
            )
            surface.blit( scaled_img, (draw_x, draw_y))
        else:
            surface.blit(current_img ,(self.x,self.y))