import os
import json
import pathlib

# Codec Filtering Options
CODEC_OPTIONS = {
    "H.264 (Compatible)": "vcodec^=avc1",
    "AV1 (Efficient)": "vcodec^=av01",
    "VP9 (Best Quality)": "vcodec^=vp9"
}

# Base format templates
# These will be used to generate the full command strings
QUALITY_FORMAT_TEMPLATES = {
    "Clips": {
        "Best Available": "bestvideo[{codec}][ext=mp4]+bestaudio[ext=m4a][asr=44100]/bestvideo[{codec}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "Up to 4K": "bestvideo[{codec}][height<=2160][ext=mp4]+bestaudio[ext=m4a][asr=44100]/bestvideo[{codec}][height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]",
        "Up to 1080p": "bestvideo[{codec}][height<=1080][ext=mp4]+bestaudio[ext=m4a][asr=44100]/bestvideo[{codec}][height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "Up to 720p": "bestvideo[{codec}][height<=720][ext=mp4]+bestaudio[ext=m4a][asr=44100]/bestvideo[{codec}][height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]"
    },
    "Proxies": {
        "360p": "bestvideo[{codec}][height<=360]+bestaudio[asr=44100]/bestvideo[{codec}][height<=360]+bestaudio/best[height<=360]",
        "480p": "bestvideo[{codec}][height<=480]+bestaudio[asr=44100]/bestvideo[{codec}][height<=480]+bestaudio/best[height<=480]",
        "720p": "bestvideo[{codec}][height<=720]+bestaudio[asr=44100]/bestvideo[{codec}][height<=720]+bestaudio/best[height<=720]",
        "1080p": "bestvideo[{codec}][height<=1080]+bestaudio[asr=44100]/bestvideo[{codec}][height<=1080]+bestaudio/best[height<=1080]"
    }
}

DEFAULT_SETTINGS = {
    "clips_quality": "Best Available",
    "proxy_quality": "360p",
    "clips_codec": "H.264 (Compatible)",
    "proxy_codec": "H.264 (Compatible)",
    "use_cookies": False,
    "cookie_file": "",
    "use_ejs": True,
    "js_runtime": "node",
    "project_folder": "",
    "format_commands": {
        "Clips": {},
        "Proxies": {}
    }
}

class AppConfig:
    def __init__(self):
        docs = pathlib.Path(os.path.expanduser('~')) / "Documents" / "PreCut" / "data"
        docs.mkdir(parents=True, exist_ok=True)
        self.config_path = docs / "settings.json"
        
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

        # Always regenerate command strings from current templates and codec settings.
        # This propagates command-template fixes to existing users without requiring
        # a manual reset.
        self.regenerate_all_commands()

    def regenerate_all_commands(self):
        self.regenerate_commands("Clips")
        self.regenerate_commands("Proxies")

    def regenerate_commands(self, category):
        # Category is 'Clips' or 'Proxies'
        # Settings keys are 'clips_codec' and 'proxy_codec'
        settings_key = "clips_codec" if category == "Clips" else "proxy_codec"
        codec_label = self.settings.get(settings_key)
        codec_filter = CODEC_OPTIONS.get(codec_label, "")
        
        # Add the brackets only if a filter exists
        filter_str = f"[{codec_filter}]" if codec_filter else ""
        
        for label, template in QUALITY_FORMAT_TEMPLATES[category].items():
            # The template itself should not have the brackets around {codec}
            # Or we change the template to not have them.
            # Current template: bestvideo[{codec}][ext=mp4]
            # My fix: Remove brackets from template and add them in filter_str
            formatted_format = template.replace("[{codec}]", "{codec}").format(codec=filter_str)
            # Store the full yt-dlp command prefix
            self.settings["format_commands"][category][label] = f"yt-dlp -f \"{formatted_format}\" --merge-output-format mp4"
        
        self.save()

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Deeply update format_commands to avoid losing keys if only one category is present
                    if "format_commands" in data:
                        for cat in ["Clips", "Proxies"]:
                            if cat in data["format_commands"]:
                                self.settings["format_commands"][cat].update(data["format_commands"][cat])
                        del data["format_commands"]
                    
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
