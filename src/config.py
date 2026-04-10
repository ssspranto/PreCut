import os
import json
import pathlib

# Configuration mappings
DEFAULT_SETTINGS = {
    "clips_quality": "Best Available",
    "proxy_quality": "360p",
    "project_folder": ""
}

QUALITY_FORMATS = {
    "Clips": {
        "Best Available": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b",
        "Up to 4K": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]",
        "Up to 1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "Up to 720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]"
    },
    "Proxies": {
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    }
}

class AppConfig:
    def __init__(self):
        docs = pathlib.Path(os.path.expanduser('~')) / "Documents" / "PreCut" / "data"
        docs.mkdir(parents=True, exist_ok=True)
        self.config_path = docs / "settings.json"
        
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception:
                pass
        else:
            self.save()

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception:
            pass
            
    def get(self, key):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))
        
    def set(self, key, value):
        self.settings[key] = value
        self.save()

# Global singleton configuration manager
app_config = AppConfig()
