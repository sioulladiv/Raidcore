import pygame
import math

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