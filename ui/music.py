import pygame
import json
import os

class Music:
    def __init__(self):
        pygame.mixer.init()
        self.music = pygame.mixer.music
        self.current_track = None
        self.current_level = None
        
        with open("data/music_data.json", "r") as f:
            self.music_data = json.load(f)

        
        self.play_menu_music()

    def music_find(self, category, track_index=0):
        if track_index >= len(self.music_data[category]):
            track_index = 0
            
        track_info = self.music_data[category][track_index]
        file_path = track_info["file"]

        if self.current_track:
            self.music.stop()
        
        self.music.load(file_path)
        self.music.set_volume(track_info.get("volume", 0.7))
        
        if track_info.get("loop", True):
            self.music.play(-1) 
        else:
            self.music.play()
            
        self.current_track = file_path
        print(f"Playing: {file_path}")


    def play_level_music(self, level):
        level_key = f"level{level}"
        if level_key != self.current_level:
            self.music_find(level_key)
            self.current_level = level_key

    def play_menu_music(self):
        if self.current_level != "menu":
            self.music_find("menu")
            self.current_level = "menu"

    def play_game_over_music(self):
        if self.current_level != "game_over":
            self.music_find("game_over")
            self.current_level = "game_over"

    def stop_music(self):
        self.music.stop()
        self.current_track = None
        self.current_level = None

    def pause_music(self):
        self.music.pause()

    def unpause_music(self):
        self.music.unpause()

    def set_volume(self, volume):
        self.music.set_volume(max(0.0, min(1.0, volume)))

    def is_playing(self):
        return self.music.get_busy()

    def update(self, level):
        self.play_level_music(level)
