import pygame
import math
import random
import json

with open("enemy_data.json", "r") as f:
    enemy_data = json.load(f)

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
        
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = data["animations"]["idle"]["frames"] * 20
        self.is_moving = False
        self.facing_dir = 0
        self.collision_width = int(self.width * 0.7)
        self.collision_height = int(self.height * 0.6)
        self.collision_offset_x = (self.width - self.collision_width) // 2
        self.collision_offset_y = self.height - self.collision_height - 2

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

    def update(self, keys, tiles, player, enemies, bullets=None):  
        if self.hit_timer > 0:
            self.hit_timer -= 1  
            if self.hit_timer < 0:
                self.hit_timer = 0 

        direction_x = player.x - self.x
        direction_y = player.y - self.y
        
        distance = (direction_x ** 2 + direction_y ** 2) ** 0.5
        self.is_moving = False

        if distance < 100 and distance > 0:
            self.is_moving = True

            direction_x /= distance
            direction_y /= distance

            dx = direction_x * self.speed * (0.5 + random.random()/2)
            dy = direction_y * self.speed * (0.5 + random.random()/2)


            if direction_x > 0:
                self.facing_dir = 1  
            else:
                self.facing_dir = 0

            self.move_and_collide(dx, dy, tiles, enemies, bullets)  

    def move_and_collide(self, dx, dy, tiles, enemies=None, bullets=None):
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
            for bullet in bullets:
                if enemy_rect.colliderect(bullet.get_rect()):
                    self.hit_timer = 10  
                    self.lives -= bullet.damage
                    bullets.remove(bullet)
                    if self.lives <= 0 and enemies is not None:
                        enemies.remove(self)

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