import pygame
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Player:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.speed = 3.5
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
            img_path = os.path.join(project_root, "Dungeon", "frames", f"agent_idle{'0' + str(i) if i < 10 else str(i)}.png")
            img = pygame.image.load(img_path)
            img = pygame.transform.scale(img, (width, height))
            self.idle_frames.append(img)  
            self.idle_frames.append(img)  

        self.walk_frames = []
        for i in range(4):
            img_path = os.path.join(project_root, "Dungeon", "frames", f"agent_running{i}.png")
            img = pygame.image.load(img_path)
            img = pygame.transform.scale(img, (width, height))
            self.walk_frames.append(img)

    def update(self, keys, tiles, endlevel_tiles, game, spike_tiles): 
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

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        
        self.move_and_collide(dx, dy, tiles, game, spike_tiles)

        for tile in endlevel_tiles:
            if self.get_rect(self.x, self.y).colliderect(tile):
                game.next_level()

    def move_and_collide(self, dx, dy, tiles, game, spike_tiles):
        self.x += dx
        player_rect = self.get_rect(self.x, self.y)
        
        for wall in tiles:
            if player_rect.colliderect(wall):
                if dx > 0:  
                    self.x = wall.left - self.collision_width - self.collision_offset_x
                elif dx < 0:  
                    self.x = wall.right - self.collision_offset_x
                break
        
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
        
        for wall in tiles:
            if player_rect.colliderect(wall):
                if dy > 0:  
                    self.y = wall.top - self.collision_height - self.collision_offset_y
                elif dy < 0: 
                    self.y = wall.bottom - self.collision_offset_y
                break
        
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