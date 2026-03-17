"""Background music controller backed by a JSON data file."""
import pygame
import json
import os
from config.game_settings import game_settings


class Music:
    """Manages background music playback keyed by level or context.

    Track metadata (file path, volume, loop flag) is stored in
    ``data/music_data.json``.  Only one track plays at a time; switching
    context calls automatically stop the previous track.
    """
    def __init__(self) -> None:
        """Initialise the mixer and start playing menu music."""
        pygame.mixer.init()
        self.music = pygame.mixer.music
        self.current_track = None
        self.current_level = None
        
        with open("data/music_data.json", "r") as f:
            self.music_data = json.load(f)

        
        self.play_menu_music()

    def music_find(self, category: str, track_index: int = 0) -> None:
        """Load and play a track by category key and optional index.

        Args:
            category: Top-level key in ``music_data.json``
                (e.g. ``'menu'``, ``'level1'``, ``'game_over'``).
            track_index: Index within the category's track list (default 0).
        """
        if track_index >= len(self.music_data[category]): track_index = 0
            
        trackinfo = self.music_data[category][track_index]
        file_path = trackinfo["file"]

        if self.current_track: self.music.stop()
        
        self.music.load(file_path)
        base_volume = trackinfo.get("volume", 0.7)
        final_volume = base_volume*game_settings.get_music_volume()
        self.music.set_volume( final_volume)
        
        # Loop indefinitely if "loop" is true in the track info, otherwise play once
        if trackinfo.get("loop", True):
            self.music.play(-1) 
        else:
            self.music.play()
            
        self.current_track = file_path
        print(f"Playing: {file_path}")


    def play_level_music(self, level: int) -> None:
        """Switch to the music track for the given level number.

        No-op when the requested track is already playing.

        Args:
            level: Level index (0-based).
        """

        level_key = f"level{level}"
        if level_key != self.current_level:
            self.music_find(level_key)
            self.current_level = level_key

    def play_menu_music(self) -> None:
        """Switch to the main menu music track."""
        if self.current_level != "menu":
            self.music_find("menu")
            self.current_level = "menu"

    def play_game_over_music(self) -> None:
        """Switch to the game-over music track."""
        if self.current_level != "game_over":
            self.music_find("game_over")
            self.current_level = "game_over"

    def stop_music(self) -> None:
        """Stop music playback entirely and reset track state."""
        self.music.stop()
        self.current_track = None
        self.current_level = None

    def pause_music(self) -> None:
        """Pause the currently playing track."""
        self.music.pause()

    def unpause_music(self) -> None:
        """Resume a paused track."""
        self.music.unpause()

    def set_volume(self, volume: float) -> None:
        """Set the playback volume.

        Args:
            volume: Volume level in the range [0.0, 1.0]; clamped automatically.
        """
        self.music.set_volume(max(0.0, min(1.0, volume)))

    def is_playing(self) -> bool:
        """Return ``True`` when music is actively playing."""
        return self.music.get_busy()

    def update(self, level: int) -> None:
        """Called each frame; switches to the appropriate level track.

        Args:
            level: Current level index.
        """
        self.play_level_music(level)
