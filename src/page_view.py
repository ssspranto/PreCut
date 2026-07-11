import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import subprocess
import re
import os
import pathlib
import shlex
import glob
import yt_dlp
import requests
from io import BytesIO
from PIL import Image
from utils import *
from config import app_config, CODEC_OPTIONS
from ui_theme import COLORS, FONTS

class DownloadCancelled(Exception):
    pass

class DownloadPaused(Exception):
    pass

def apply_cookie_option(ydl_opts):
    # Disable color codes to keep UI text clean
    ydl_opts["no_color"] = True
    
    # Apply Cookie settings
    use_cookies = bool(app_config.get("use_cookies"))
    cookie_file = str(app_config.get("cookie_file") or "").strip()
    if use_cookies and cookie_file:
        ydl_opts["cookiefile"] = os.path.normpath(cookie_file).replace("\\", "/")

    # Apply EJS (External JS) settings to solve JS challenges
    if bool(app_config.get("use_ejs")):
        ydl_opts["remote_components"] = ["ejs:github"]
        runtime = app_config.get("js_runtime")
        if runtime:
            # The API expects a dict of {runtime_name: config_dict}
            ydl_opts["js_runtimes"] = {runtime: {}}

def extract_format_selector(command_prefix):
    parts = shlex.split(command_prefix)
    for idx, part in enumerate(parts):
        if part in ("-f", "--format") and idx + 1 < len(parts):
            return parts[idx + 1]
    return None

class YdlPanelLogger:
    def __init__(self, panel):
        self.panel = panel

    def debug(self, msg):
        self.panel.queue_log(f"{msg}\n")

    def warning(self, msg):
        self.panel.queue_log(f"WARNING: {msg}\n")

    def error(self, msg):
        self.panel.queue_log(f"ERROR: {msg}\n")

class DownloadCard(ctk.CTkFrame):
    def __init__(self, master, url, ydl_opts, on_finish_callback=None, **kw):
        if 'fg_color' not in kw:
            kw['fg_color'] = COLORS["bg_card"]
        super().__init__(master, corner_radius=12, **kw)
        
        self.url = url
        self.ydl_opts = dict(ydl_opts)
        self.on_finish_callback = on_finish_callback
        self.cancel_requested = False
        self._closed = False
        self.downloaded_files = []
        self.show_logs = False

        # Content Layout
        self.grid_columnconfigure(1, weight=1)

        # Thumbnail (Placeholder)
        self.thumb_label = ctk.CTkLabel(self, text="🎬", font=("Inter", 24), width=100, height=70, fg_color="#2B2B2B", corner_radius=8)
        self.thumb_label.grid(row=0, column=0, rowspan=2, padx=15, pady=15, sticky="n")

        # Info & Progress Area
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)

        self.title_label = ctk.CTkLabel(self.info_frame, text="Analyzing video...", font=FONTS["body_bold"], text_color="white", anchor="w")
        self.title_label.pack(fill=tk.X)

        self.progress_bar = ctk.CTkProgressBar(self.info_frame, orientation="horizontal", height=8, progress_color=COLORS["accent_crimson"])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill=tk.X, pady=(10, 5))

        self.status_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.status_frame.pack(fill=tk.X)

        self.speed_label = ctk.CTkLabel(self.status_frame, text="Speed: --", font=FONTS["small"], text_color=COLORS["text_dim"])
        self.speed_label.pack(side=tk.LEFT)

        self.size_label = ctk.CTkLabel(self.status_frame, text="-- / --", font=FONTS["small"], text_color=COLORS["text_dim"])
        self.size_label.pack(side=tk.RIGHT)

        # Action Area
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=0, column=2, rowspan=2, padx=15, pady=15, sticky="ne")

        self.cancel_btn = ctk.CTkButton(self.actions_frame, text="Cancel", width=80, height=30, fg_color="#3E3E42", hover_color=COLORS["accent_crimson"], command=self.stop_download)
        self.cancel_btn.pack(pady=(0, 10))

        self.pause_btn = ctk.CTkButton(self.actions_frame, text="Pause", width=80, height=30, fg_color="transparent", border_width=1, border_color="#3E3E42", command=self.toggle_pause)
        self.pause_btn.pack(pady=(0, 10))

        self.log_btn = ctk.CTkButton(self.actions_frame, text="Logs", width=80, height=30, fg_color="transparent", border_width=1, border_color="#3E3E42", command=self.toggle_logs)
        self.log_btn.pack()

        # Collapsible Log Box
        self.log_box = ctk.CTkTextbox(self, height=0, fg_color="#1E1E1E", text_color="#A0A0A0", font=("Consolas", 11), border_color="#3E3E42", border_width=1)
        self.log_box.grid(row=2, column=0, columnspan=3, padx=15, pady=(0, 15), sticky="nsew")
        self.log_box.grid_remove() # Hidden by default

        self.is_paused = False
        self._last_thumb_url = None
        self.download_thread = threading.Thread(target=self.start_download, daemon=True)
        self.download_thread.start()

    def toggle_logs(self):
        self.show_logs = not self.show_logs
        if self.show_logs:
            self.log_box.grid()
            self.log_box.configure(height=120)
        else:
            self.log_box.grid_remove()

    def start_download(self):
        try:
            runtime_opts = dict(self.ydl_opts)
            runtime_opts["logger"] = YdlPanelLogger(self)
            runtime_opts["progress_hooks"] = [self.on_progress_update]
            
            # Fetch metadata first to get Title/Thumbnail
            with yt_dlp.YoutubeDL(runtime_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                # Check if it's a playlist to provide a better initial title
                is_playlist = info.get('_type') == 'playlist'
                title = info.get("title", "Unknown Video")
                if is_playlist:
                    title = f"Playlist: {title}"
                
                thumb_url = info.get("thumbnail")
                self._last_thumb_url = thumb_url
                
                self.after(0, lambda t=title: self.title_label.configure(text=t))
                
                if thumb_url:
                    threading.Thread(target=self.load_thumbnail, args=(thumb_url,), daemon=True).start()

                # Start actual download
                ydl.download([self.url])

            if self.cancel_requested:
                self.queue_log("[download] Cancelled by user.\n")
                self.after(0, self._close_panel)
                return

            self.normalize_downloaded_audio()
            self.after(0, self.on_finish)
        except (DownloadCancelled, DownloadPaused) as e:
            if isinstance(e, DownloadPaused):
                self.queue_log("[download] Paused by user.\n")
                self.after(0, lambda: self.speed_label.configure(text="Status: Paused", text_color=COLORS["accent_crimson"]))
            else:
                self.queue_log("[download] Cancelled by user.\n")
                self.after(0, self._close_panel)
        except yt_dlp.utils.DownloadError as e:
            if not self.cancel_requested:
                self.after(0, lambda err=e: messagebox.showerror("Download Error", str(err)))
                self.after(0, self._close_panel)
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Download Error", str(err)))
            self.after(0, self._close_panel)

    def load_thumbnail(self, url):
        try:
            # Add a user-agent to avoid being blocked by some CDNs
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, timeout=10, headers=headers)
            img_data = BytesIO(response.content)
            pil_img = Image.open(img_data)
            
            # Create CTkImage for scaling
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 70))
            
            if self.winfo_exists():
                # We MUST keep a reference to the image object or it gets garbage collected
                self.thumbnail_ref = ctk_img 
                self.after(0, self._safe_update_thumbnail)
        except Exception as e:
            print(f"Thumbnail load error: {e}")

    def _safe_update_thumbnail(self):
        """Safely update the UI only if the widget still exists"""
        try:
            if self.winfo_exists() and hasattr(self, 'thumbnail_ref'):
                self.thumb_label.configure(image=self.thumbnail_ref, text="")
        except Exception:
            pass # Widget likely destroyed during update


    def on_finish(self):
        messagebox.showinfo("Download Completed!", "Video files have been successfully downloaded.")
        self._close_panel()

    def append_log(self, text):
        if not self.winfo_exists():
            return
        self.log_box.configure(state='normal')
        self.log_box.insert(tk.END, text)
        self.log_box.see(tk.END)
        self.log_box.configure(state='disabled')

    def toggle_pause(self):
        if not self.is_paused:
            # Pausing
            self.is_paused = True
            self.pause_btn.configure(text="Resume", fg_color=COLORS["accent_crimson"], text_color="white")
            self.queue_log("[download] Pausing...\n")
        else:
            # Resuming
            self.is_paused = False
            self.pause_btn.configure(text="Pause", fg_color="transparent", text_color="white")
            self.queue_log("[download] Resuming...\n")
            self.speed_label.configure(text="Speed: Resuming...", text_color=COLORS["text_dim"])
            # Start a new thread to resume
            self.download_thread = threading.Thread(target=self.start_download, daemon=True)
            self.download_thread.start()

    def stop_download(self):
        self.cancel_requested = True
        self.queue_log("[download] Cancel requested...\n")
        self._close_panel()

    def _close_panel(self):
        if self._closed:
            return
        self._closed = True
        if self.on_finish_callback:
            self.on_finish_callback(self)
        if self.winfo_exists():
            self.destroy()

    def update_progress(self, percentage, speed, size_info):
        if not self.winfo_exists():
            return
        self.progress_bar.set(percentage / 100)
        self.speed_label.configure(text=f'Speed: {speed}')
        self.size_label.configure(text=size_info)

    def queue_log(self, text):
        if self.winfo_exists():
            self.after(0, lambda t=text: self.append_log(t))

    def on_progress_update(self, data):
        if self.cancel_requested:
            raise DownloadCancelled()
        if self.is_paused:
            raise DownloadPaused()

        # Update title/thumbnail dynamically (crucial for playlists)
        info_dict = data.get("info_dict", {})
        if info_dict:
            new_title = info_dict.get("title")
            # Only update if the title is actually different to avoid flickering
            if new_title and new_title != self.title_label.cget("text"):
                self.after(0, lambda t=new_title: self.title_label.configure(text=t))
            
            new_thumb = info_dict.get("thumbnail")
            if new_thumb and self._last_thumb_url != new_thumb:
                self._last_thumb_url = new_thumb
                threading.Thread(target=self.load_thumbnail, args=(new_thumb,), daemon=True).start()

        status = data.get("status")
        if status == "downloading":
            percentage = self._percent_to_float(data.get("_percent_str"))
            speed = data.get("_speed_str", "N/A")
            
            downloaded = data.get("_downloaded_bytes_str", "0B")
            total = data.get("_total_bytes_str") or data.get("_total_bytes_estimate_str", "N/A")
            size_info = f"{downloaded} / {total}"
            
            self.after(0, lambda p=percentage, s=speed, si=size_info: self.update_progress(p, s, si))
        elif status == "finished":
            final_file = data.get("filename")
            if final_file and final_file not in self.downloaded_files:
                self.downloaded_files.append(final_file)

    def _percent_to_float(self, percent_str):
        if not percent_str:
            return 0.0
        cleaned = percent_str.replace("%", "").strip()
        try:
            return float(cleaned)
        except Exception:
            return 0.0

    def normalize_downloaded_audio(self):
        """
        Fallback: ensure every downloaded file ends with 44.1 kHz audio.
        We first prefer native 44.1 kHz streams in yt-dlp format selection;
        this post-step only re-encodes when the output is not already 44100 Hz.
        """
        unique_paths = []
        for path in self.downloaded_files:
            if path not in unique_paths:
                unique_paths.append(path)

        for media_path in unique_paths:
            if not os.path.exists(media_path):
                continue

            sample_rate = self.get_audio_sample_rate(media_path)
            if sample_rate == 44100:
                continue

            base, ext = os.path.splitext(media_path)
            temp_path = f"{base}_srfix{ext}"
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i", media_path,
                "-map", "0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-ar", "44100",
                temp_path
            ]

            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NO_WINDOW

            try:
                self.queue_log(f"[post] Resampling audio to 44.1kHz: {os.path.basename(media_path)}\n")
                result = subprocess.run(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=creation_flags
                )
                self.queue_log(result.stdout)

                if result.returncode == 0 and os.path.exists(temp_path):
                    os.replace(temp_path, media_path)
                elif os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.queue_log(f"[post] Failed to normalize sample rate: {e}\n")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    def get_audio_sample_rate(self, media_path):
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            media_path
        ]

        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            result = subprocess.run(
                probe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )
            if result.returncode != 0:
                return None
            value = result.stdout.strip()
            return int(value) if value.isdigit() else None
        except Exception:
            return None

class Page(ctk.CTkFrame):
    project_location = ""
    def __init__(self, master, **kw):
        if 'fg_color' not in kw:
            kw['fg_color'] = '#1A1A1D'
        super().__init__(master, **kw)

class TranscriptGenerator(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        """
        Create the widgets specific to this service (TranscriptGenerator)
        """
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        # url location
        ctk.CTkLabel(self.frame_content, text="Enter Video Link:", font=FONTS["header"], text_color='white').pack(anchor="w", padx=30, pady=(40, 5))
        
        self.url_box = ctk.CTkEntry(
            self.frame_content, 
            fg_color='#2B2B2B', 
            text_color='white', 
            border_color='#3E3E42',
            border_width=1,
            font=FONTS["body"], 
            placeholder_text="https://www.youtube.com/watch?v=..."
        )
        self.url_box.pack(fill=tk.X, padx=30, pady=(0, 20), ipady=8)

        # transcript button
        self.btn_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        self.btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        self.transcript_button = ctk.CTkButton(
            self.btn_frame, 
            text="Transcript It", 
            font=FONTS["body_bold"],
            fg_color=COLORS["accent_crimson"], 
            hover_color=COLORS["accent_glow"],
            corner_radius=8,
            command=self.generate
        )
        self.transcript_button.pack(side=tk.LEFT, ipady=8, ipadx=40)
        
        self.status_label = ctk.CTkLabel(self.btn_frame, text="", font=FONTS["small"], text_color="#AAAAAA")
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Output Text Box (We'll use a standard tk.Text inside a CTkFrame for better scroll control if needed, 
        # or just ctk.CTkTextbox)
        self.text_box = ctk.CTkTextbox(
            self.frame_content, 
            fg_color='#2B2B2B', 
            text_color='white', 
            font=FONTS["body"], 
            border_color='#3E3E42',
            border_width=1,
            corner_radius=8,
            state="disabled"
        )
        self.text_box.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))

        return self.frame_content

    def generate(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        url = self.url_box.get().strip()
        if not url:
            messagebox.showerror("Error", "Please provide a video URL.")
            return

        self.transcript_button.configure(state="disabled", fg_color="#888888")
        self.status_label.configure(text="Fetching transcript...")
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", tk.END)
        self.text_box.configure(state="disabled")

        import threading
        t = threading.Thread(target=self.fetch_and_process, args=(url,))
        t.daemon = True
        t.start()

    def fetch_and_process(self, url):
        import re
        
        script_dir = pathlib.Path(Page.project_location) / "Script"
        script_dir.mkdir(parents=True, exist_ok=True)
        
        # Temp vtt file
        temp_out = script_dir / "temp_transcript"

        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "writesubtitles": True,
            "subtitleslangs": ["en.*"],
            "outtmpl": str(temp_out) + ".%(ext)s",
            "quiet": True,
            "no_warnings": False
        }
        apply_cookie_option(ydl_opts)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            self.after(0, lambda: self.on_error(f"Failed to fetch transcript: {e}"))
            return

        if not self.winfo_exists():
            return

        # Find the downloaded vtt
        vtt_files = glob.glob(str(script_dir / "temp_transcript*.vtt"))
        
        if not vtt_files:
            self.after(0, lambda: self.on_error("Failed to fetch transcript (no subtitles found)."))
            return
            
        # We read from the first one found
        try:
            with open(vtt_files[0], "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.after(0, lambda: self.on_error(f"Failed to read vtt file: {e}"))
            return
        
        # Cleanup ALL temp vtt files
        for f in vtt_files:
            try:
                os.remove(f)
            except:
                pass

        # Simple Regex to clean VTT
        # Remove WebVTT formatting headers
        content = re.sub(r"^WEBVTT.*?\n", "", content, flags=re.MULTILINE|re.DOTALL)
        content = re.sub(r"Kind: captions\nLanguage: en.*?\n", "", content, flags=re.MULTILINE|re.IGNORECASE)
        # Remove timestamps
        content = re.sub(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}.*?\n", "", content, flags=re.MULTILINE)
        # Remove tags inline
        content = re.sub(r"<[^>]+>", "", content)
        
        # Extract raw text and skip duplicates across lines
        lines = content.split('\n')
        clean_words = []
        for line in lines:
            line = line.strip()
            # Ignore empty lines and numeric indexes
            if not line or line.isdigit():
                continue
            if clean_words and clean_words[-1] == line:
                continue
            clean_words.append(line)
            
        final_script = " ".join(clean_words).replace('\n', ' ').replace('\r', ' ')

        # Write to script.txt
        final_path = script_dir / "script.txt"
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(final_script)
            
        self.after(0, lambda: self.on_success(final_script, final_path))

    def on_error(self, message):
        if not self.winfo_exists():
            return
        self.transcript_button.configure(state="normal", fg_color=COLORS["accent_crimson"])
        self.status_label.configure(text="")
        messagebox.showerror("Error", message)

    def on_success(self, text, path):
        if not self.winfo_exists():
            return
        self.transcript_button.configure(state="normal", fg_color=COLORS["accent_crimson"])
        self.status_label.configure(text="Success!")
        
        self.text_box.configure(state="normal")
        self.text_box.insert("1.0", text)
        self.text_box.configure(state="disabled")
        
        try:
            os.startfile(str(path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file automatically: {e}")
        


class ClipsDownloader(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        """
        Create the widgets specific to this service (Clips Downloader)
        """
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        #url location
        ctk.CTkLabel(self.frame_content, text="Enter Video/Playlist URL for Clips:", font=FONTS["header"], text_color='white').pack(anchor="w", padx=30, pady=(40, 5))
        
        self.url_box = ctk.CTkEntry(
            self.frame_content, 
            fg_color='#2B2B2B', 
            text_color='white', 
            border_color='#3E3E42',
            border_width=1,
            font=FONTS["body"],
            placeholder_text="https://..."
        )
        self.url_box.pack(fill=tk.X, padx=30, pady=(0, 20), ipady=8)

        #buttons frame
        buttons_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20))

        #download button
        self.download_button = ctk.CTkButton(
            buttons_frame, 
            text="Download Clips", 
            font=FONTS["body_bold"],
            fg_color=COLORS["accent_crimson"], 
            hover_color=COLORS["accent_glow"],
            corner_radius=8,
            command=self.download
        )
        self.download_button.pack(side=tk.LEFT, padx=(0, 15), ipady=8, ipadx=30)

        #show downloads button
        self.show_dir_button = ctk.CTkButton(
            buttons_frame, 
            text="Show Downloads", 
            font=FONTS["body_bold"],
            fg_color='#3E3E42', 
            hover_color='#4A4A4F',
            corner_radius=8,
            command=self.open_downloads_folder
        )
        self.show_dir_button.pack(side=tk.LEFT, ipady=8, ipadx=20)

        self.panels_frame = ctk.CTkScrollableFrame(self.frame_content, fg_color="transparent", label_text="Active Downloads", label_font=FONTS["small"])
        self.panels_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 10))

        self.active_downloads = {}
        return self.frame_content

    def download(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        url = str(self.url_box.get()).strip()
        if re.match(video_regex, url) is None:
            messagebox.showerror('Invalid Link', "Please enter a valid video/playlist URL")
            return

        if url in self.active_downloads.values():
            messagebox.showwarning('Duplicate Download', "This URL is already being downloaded!")
            return

        if len(self.active_downloads) >= 2:
            messagebox.showwarning('Limit Reached', "You can only run a maximum of 2 downloads at a time.")
            return

        quality_key = app_config.get("clips_quality")
        format_commands = app_config.get("format_commands")
        command_prefix = format_commands["Clips"].get(quality_key)
        
        if not command_prefix:
            # Fallback if command is missing for some reason
            messagebox.showerror("Error", "Selected format command not found. Please reset settings.")
            return

        format_selector = extract_format_selector(command_prefix)
        if not format_selector:
            messagebox.showerror("Command Error", "Failed to parse selected format command.")
            return

        output_path = str(pathlib.Path(Page.project_location) / "Clips" / "%(title)s.%(ext)s")
        ydl_opts = {
            "format": format_selector,
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": False
        }
        apply_cookie_option(ydl_opts)

        panel = DownloadCard(self.panels_frame, url, ydl_opts, on_finish_callback=self.on_download_complete)
        panel.pack(fill=tk.X, padx=30, pady=(0, 10))
        self.active_downloads[panel] = url

    def on_download_complete(self, panel):
        if panel in self.active_downloads:
            del self.active_downloads[panel]

    def open_downloads_folder(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        target_dir = pathlib.Path(Page.project_location) / "Clips"
        target_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(target_dir))

class ProxyDownloader(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        """
        Create the widgets specific to this service (Proxy Downloader)
        """
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        #url location
        ctk.CTkLabel(self.frame_content, text="Enter Video/Playlist URL for Proxy:", font=FONTS["header"], text_color='white').pack(anchor="w", padx=30, pady=(40, 5))
        
        self.url_box = ctk.CTkEntry(
            self.frame_content, 
            fg_color='#2B2B2B', 
            text_color='white', 
            border_color='#3E3E42',
            border_width=1,
            font=FONTS["body"],
            placeholder_text="https://..."
        )
        self.url_box.pack(fill=tk.X, padx=30, pady=(0, 20), ipady=8)

        #buttons frame
        buttons_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20))

        #download button
        self.download_button = ctk.CTkButton(
            buttons_frame, 
            text="Download Proxy", 
            font=FONTS["body_bold"],
            fg_color=COLORS["accent_crimson"], 
            hover_color=COLORS["accent_glow"],
            corner_radius=8,
            command=self.download
        )
        self.download_button.pack(side=tk.LEFT, padx=(0, 15), ipady=8, ipadx=30)

        #show downloads button
        self.show_dir_button = ctk.CTkButton(
            buttons_frame, 
            text="Show Downloads", 
            font=FONTS["body_bold"],
            fg_color='#3E3E42', 
            hover_color='#4A4A4F',
            corner_radius=8,
            command=self.open_downloads_folder
        )
        self.show_dir_button.pack(side=tk.LEFT, ipady=8, ipadx=20)

        self.panels_frame = ctk.CTkScrollableFrame(self.frame_content, fg_color="transparent", label_text="Active Proxies", label_font=FONTS["small"])
        self.panels_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 10))

        self.active_downloads = {}
        return self.frame_content

    def download(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        url = str(self.url_box.get()).strip()
        if re.match(video_regex, url) is None:
            messagebox.showerror('Invalid Link', "Please enter a valid video/playlist URL")
            return

        if url in self.active_downloads.values():
            messagebox.showwarning('Duplicate Download', "This URL is already being downloaded!")
            return

        if len(self.active_downloads) >= 2:
            messagebox.showwarning('Limit Reached', "You can only run a maximum of 2 downloads at a time.")
            return

        quality_key = app_config.get("proxy_quality")
        format_commands = app_config.get("format_commands")
        command_prefix = format_commands["Proxies"].get(quality_key)

        if not command_prefix:
            messagebox.showerror("Error", "Selected format command not found. Please reset settings.")
            return

        format_selector = extract_format_selector(command_prefix)
        if not format_selector:
            messagebox.showerror("Command Error", "Failed to parse selected format command.")
            return

        output_path = str(pathlib.Path(Page.project_location) / "Proxies" / "%(title)s_Proxy.%(ext)s")
        ydl_opts = {
            "format": format_selector,
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": False
        }
        apply_cookie_option(ydl_opts)

        panel = DownloadCard(self.panels_frame, url, ydl_opts, on_finish_callback=self.on_download_complete)
        panel.pack(fill=tk.X, padx=30, pady=(0, 10))
        self.active_downloads[panel] = url

    def on_download_complete(self, panel):
        if panel in self.active_downloads:
            del self.active_downloads[panel]

    def open_downloads_folder(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        target_dir = pathlib.Path(Page.project_location) / "Proxies"
        target_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(target_dir))

class Home(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        # project folder location entry
        ctk.CTkLabel(self.frame_content, text="Project Folder Location:", font=FONTS["header"], text_color='white').pack(anchor="w", padx=30, pady=(40, 5))
        
        # Frame for entry and button
        location_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        location_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        self.project_location_entry = ctk.CTkEntry(
            location_frame, 
            fg_color='#2B2B2B', 
            text_color='white', 
            placeholder_text="Select your project directory...",
            border_color='#3E3E42',
            border_width=1,
            font=FONTS["body"],
            state="disabled"
        )
        self.project_location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        
        saved_folder = app_config.get("project_folder")
        if saved_folder:
            Page.project_location = saved_folder
            self.project_location_entry.configure(state='normal')
            self.project_location_entry.insert(0, saved_folder)
            self.project_location_entry.configure(state='disabled')

        # The select button
        self.select_button = ctk.CTkButton(
            location_frame, 
            text='Select', 
            command=self.select_project_folder, 
            font=FONTS["body_bold"],
            fg_color=COLORS["accent_crimson"], 
            hover_color=COLORS["accent_glow"],
            corner_radius=8,
            width=100
        )
        self.select_button.pack(side=tk.LEFT, ipady=8, ipadx=15)

        return self.frame_content

    def select_project_folder(self):
        folder = filedialog.askdirectory(title="Select Project Folder")
        if folder:
            Page.project_location = folder
            self.project_location_entry.configure(state='normal')
            self.project_location_entry.delete(0, tk.END)
            self.project_location_entry.insert(0, folder)
            self.project_location_entry.configure(state='disabled')
            app_config.set("project_folder", folder)

class Settings(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        # Title
        ctk.CTkLabel(self.frame_content, text="Application Settings", font=FONTS["title"], text_color='white').pack(anchor="w", padx=30, pady=(40, 20))

        # Proxy Quality & Codec
        proxy_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        proxy_frame.pack(fill=tk.X, padx=30, pady=10)
        
        ctk.CTkLabel(proxy_frame, text="Proxy Quality: ", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 20))
        self.proxy_var = tk.StringVar(value=app_config.get("proxy_quality"))
        proxy_opts = list(app_config.get("format_commands")["Proxies"].keys())
        self.proxy_cb = ctk.CTkComboBox(proxy_frame, variable=self.proxy_var, values=proxy_opts, state="readonly", font=FONTS["body"], width=200)
        self.proxy_cb.pack(side=tk.LEFT)

        ctk.CTkLabel(proxy_frame, text="Codec: ", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(30, 10))
        self.proxy_codec_var = tk.StringVar(value=app_config.get("proxy_codec"))
        codec_opts = list(CODEC_OPTIONS.keys())
        self.proxy_codec_cb = ctk.CTkComboBox(proxy_frame, variable=self.proxy_codec_var, values=codec_opts, state="readonly", font=FONTS["body"], width=200)
        self.proxy_codec_cb.pack(side=tk.LEFT)

        # Clips Quality & Codec
        clips_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        clips_frame.pack(fill=tk.X, padx=30, pady=10)

        ctk.CTkLabel(clips_frame, text="Clips Quality: ", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 20))
        self.clips_var = tk.StringVar(value=app_config.get("clips_quality"))
        clips_opts = list(app_config.get("format_commands")["Clips"].keys())
        self.clips_cb = ctk.CTkComboBox(clips_frame, variable=self.clips_var, values=clips_opts, state="readonly", font=FONTS["body"], width=200)
        self.clips_cb.pack(side=tk.LEFT)

        ctk.CTkLabel(clips_frame, text="Codec: ", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(30, 10))
        self.clips_codec_var = tk.StringVar(value=app_config.get("clips_codec"))
        self.clips_codec_cb = ctk.CTkComboBox(clips_frame, variable=self.clips_codec_var, values=codec_opts, state="readonly", font=FONTS["body"], width=200)
        self.clips_codec_cb.pack(side=tk.LEFT)

        # Cookies Authentication
        cookies_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        cookies_frame.pack(fill=tk.X, padx=30, pady=10)

        self.use_cookies_var = tk.BooleanVar(value=bool(app_config.get("use_cookies")))
        self.use_cookies_cb = ctk.CTkCheckBox(
            cookies_frame,
            text="Use Cookies for yt-dlp",
            variable=self.use_cookies_var,
            command=self.on_cookies_toggle,
            fg_color=COLORS["accent_crimson"],
            hover_color=COLORS["accent_glow"],
            font=FONTS["body_bold"]
        )
        self.use_cookies_cb.pack(side=tk.LEFT, padx=(0, 20))

        self.cookie_file_var = tk.StringVar(value=str(app_config.get("cookie_file") or ""))
        self.cookie_entry = ctk.CTkEntry(
            cookies_frame,
            textvariable=self.cookie_file_var,
            fg_color='#2B2B2B',
            text_color='white',
            border_color='#3E3E42',
            border_width=1,
            font=FONTS["body"],
            state="disabled"
        )
        self.cookie_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=6)

        self.cookie_select_button = ctk.CTkButton(
            cookies_frame,
            text='Select Cookie File',
            command=self.select_cookie_file,
            font=FONTS["body_bold"],
            fg_color=COLORS["accent_crimson"],
            hover_color=COLORS["accent_glow"],
            corner_radius=8,
            width=150
        )
        self.cookie_select_button.pack(side=tk.LEFT, ipady=6, ipadx=12)
        self.on_cookies_toggle()

        # EJS Challenge Solver
        ejs_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        ejs_frame.pack(fill=tk.X, padx=30, pady=10)

        self.use_ejs_var = tk.BooleanVar(value=bool(app_config.get("use_ejs")))
        self.use_ejs_cb = ctk.CTkCheckBox(
            ejs_frame,
            text="Solve JS Challenges (EJS)",
            variable=self.use_ejs_var,
            command=self.on_ejs_toggle,
            fg_color=COLORS["accent_crimson"],
            hover_color=COLORS["accent_glow"],
            font=FONTS["body_bold"]
        )
        self.use_ejs_cb.pack(side=tk.LEFT, padx=(0, 20))

        ctk.CTkLabel(ejs_frame, text="JS Runtime: ", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT)
        self.available_runtimes = get_available_js_runtimes()
        self.js_runtime_var = tk.StringVar(value=app_config.get("js_runtime") or "node")
        
        # If saved runtime is not available, pick the first available one
        if self.js_runtime_var.get() not in self.available_runtimes and self.available_runtimes:
            self.js_runtime_var.set(self.available_runtimes[0])

        self.js_runtime_cb = ctk.CTkComboBox(ejs_frame, variable=self.js_runtime_var, values=self.available_runtimes if self.available_runtimes else ["None Found"], state="readonly", font=FONTS["body"], width=150)
        self.js_runtime_cb.pack(side=tk.LEFT, padx=10)
        
        # Initial validation
        self.on_ejs_toggle(initial=True)

        # Buttons
        buttons_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        buttons_frame.pack(fill=tk.X, padx=30, pady=40)

        self.save_button = ctk.CTkButton(buttons_frame, text="Save Settings", font=FONTS["header"], fg_color=COLORS["accent_crimson"], hover_color=COLORS["accent_glow"], corner_radius=8, command=self.save_settings)
        self.save_button.pack(side=tk.LEFT, ipady=6, ipadx=20)

        self.reset_button = ctk.CTkButton(buttons_frame, text="Reset Defaults", font=FONTS["header"], fg_color='#3E3E42', hover_color='#4A4A4F', corner_radius=8, command=self.reset_settings)
        self.reset_button.pack(side=tk.LEFT, padx=20, ipady=6, ipadx=20)

        return self.frame_content

    def on_cookies_toggle(self):
        is_enabled = self.use_cookies_var.get()
        if is_enabled:
            self.cookie_entry.configure(state='normal')
            self.cookie_select_button.configure(state='normal', fg_color=COLORS["accent_crimson"])
        else:
            self.cookie_entry.configure(state='disabled')
            self.cookie_select_button.configure(state='disabled', fg_color='#3E3E42')

    def on_ejs_toggle(self, initial=False):
        if not self.available_runtimes:
            if not initial and self.use_ejs_var.get():
                messagebox.showerror("Runtime Missing", "No JavaScript runtime (Node, Deno, Bun, or QuickJS) was detected on your system. EJS cannot be enabled.")
            self.use_ejs_var.set(False)
            self.js_runtime_cb.configure(state='disabled')
            return

        is_enabled = self.use_ejs_var.get()
        if is_enabled:
            self.js_runtime_cb.configure(state='readonly')
        else:
            self.js_runtime_cb.configure(state='disabled')

    def select_cookie_file(self):
        selected_file = filedialog.askopenfilename(
            title="Select yt-dlp Cookies File",
            filetypes=[("Text and Cookies Files", "*.txt *.cookies"), ("All Files", "*.*")]
        )
        if selected_file:
            self.cookie_file_var.set(selected_file)

    def save_settings(self):
        old_proxy_codec = app_config.get("proxy_codec")
        old_clips_codec = app_config.get("clips_codec")
        
        new_proxy_codec = self.proxy_codec_var.get()
        new_clips_codec = self.clips_codec_var.get()
        use_cookies = self.use_cookies_var.get()
        cookie_file = self.cookie_file_var.get().strip()

        if use_cookies:
            if not cookie_file:
                messagebox.showerror("Settings Error", "Please select a cookie file or disable cookies.")
                return
            if not os.path.isfile(cookie_file):
                messagebox.showerror("Settings Error", "Selected cookie file does not exist.")
                return
        
        use_ejs = self.use_ejs_var.get()
        js_runtime = self.js_runtime_var.get()

        if use_ejs and (not self.available_runtimes or js_runtime == "None Found"):
            messagebox.showerror("Settings Error", "Please install a JS runtime to use EJS.")
            return

        app_config.set("proxy_quality", self.proxy_var.get())
        app_config.set("clips_quality", self.clips_var.get())
        app_config.set("proxy_codec", new_proxy_codec)
        app_config.set("clips_codec", new_clips_codec)
        app_config.set("use_cookies", use_cookies)
        app_config.set("cookie_file", cookie_file)
        app_config.set("use_ejs", use_ejs)
        app_config.set("js_runtime", js_runtime)
        
        # If codec changed, regenerate relevant commands
        if old_proxy_codec != new_proxy_codec:
            app_config.regenerate_commands("Proxies")
        if old_clips_codec != new_clips_codec:
            app_config.regenerate_commands("Clips")
            
        messagebox.showinfo("Success", "Settings have been safely updated.")

    def reset_settings(self):
        self.proxy_var.set("360p")
        self.clips_var.set("Best Available")
        self.proxy_codec_var.set("H.264 (Compatible)")
        self.clips_codec_var.set("H.264 (Compatible)")
        self.use_cookies_var.set(False)
        self.cookie_file_var.set("")
        self.on_cookies_toggle()
        
        app_config.set("proxy_quality", "360p")
        app_config.set("clips_quality", "Best Available")
        app_config.set("proxy_codec", "H.264 (Compatible)")
        app_config.set("clips_codec", "H.264 (Compatible)")
        app_config.set("use_cookies", False)
        app_config.set("cookie_file", "")
        app_config.set("use_ejs", True)
        app_config.set("js_runtime", "node")
        
        app_config.regenerate_all_commands()
        
        messagebox.showinfo("Reset", "Settings have been reverted to defaults.")