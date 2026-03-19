import json
import os


class Settings:
    """Manages user-configurable settings (volumes, FPS cap, VSync).

    Settings are persisted to ``config/settings.json`` and default values are
    used when the file is missing or a key is absent.
    """

    def __init__(self) -> None:
        self.settings_file = "config/settings.json"
        self.default_settings = {
            "master_volume": 50,
            "music_volume": 50,
            "sfx_volume": 50,
            "fps_cap" : 60
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> dict:
        """Load settings from file, create default if file doesn't exist"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                # Ensure all required keys exist
                for key in self.default_settings:
                    if key not in settings:
                        settings[key] = self.default_settings[key]
                return settings
            except:
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()
    
    def save_settings(self) -> None:
        """Save current settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def get_master_volume(self) -> float:
        """Get master volume as a float from 0.0 to 1.0"""
        return self.settings["master_volume"] / 100.0   
    
    def get_music_volume(self) -> float:
        """Get music volume as a float from 0.0 to 1.0"""
        return (self.settings["music_volume"] / 100.0) * self.get_master_volume()
    
    def get_sfx_volume(self) -> float:
        """Get SFX volume as a float from 0.0 to 1.0"""
        return (self.settings["sfx_volume"] / 100.0) * self.get_master_volume()
    
    def set_master_volume(self, volume: int | float) -> None:
        """Set master volume (0-100)"""
        self.settings["master_volume"] = max(0, min(100, volume))
    
    def set_music_volume(self, volume: int | float) -> None:
        """Set music volume (0-100)"""
        self.settings["music_volume"] = max(0, min(100, volume))
    
    def set_sfx_volume(self, volume: int | float) -> None:
        """Set SFX volume (0-100)"""
        self.settings["sfx_volume"] = max(0, min(100, volume))
    
    def update_from_sliders(self, master_slider: object, music_slider: object, sfx_slider: object) -> None:
        """Update volumes from menu ``Slider`` widgets and persist them.

        Args:
            master_slider: Slider controlling master volume.
            music_slider: Slider controlling music volume.
            sfx_slider: Slider controlling SFX volume.
        """
        self.set_master_volume(master_slider.value)
        self.set_music_volume(music_slider.value)
        self.set_sfx_volume(sfx_slider.value)
        self.save_settings()
    
    def get_fps_cap(self) -> int:
        """Return the configured FPS cap (0 means uncapped)."""
        return self.settings.get("fps_cap", 144)
    
    def set_fps_cap(self, fps: int) -> None:
        """Set FPS cap.  Pass 0 to uncap the frame rate."""
        self.settings["fps_cap"] = max(0, fps)
        self.save_settings()
    
    def get_vsync(self) -> bool:
        """Return whether VSync is enabled (defaults to ``False``)."""
        return self.settings.get("vsync", False)
    
    def set_vsync(self, enabled: bool) -> None:
        """Enable or disable VSync."""
        self.settings["vsync"] = enabled
        self.save_settings()

# Global settings instance
game_settings = Settings()