import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import re
import os
import pathlib
import subprocess

from ui_page import Page, apply_cookie_option, extract_format_selector
from components import DownloadCard
from config import app_config
from utils import video_regex
from ui_theme import COLORS, FONTS
import yt_dlp




class ProxyDownloader(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

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

        options_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        options_frame.pack(anchor="w", padx=30, pady=(0, 20))

        ctk.CTkLabel(options_frame, text="Quality:", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 10))
        self.quality_var = tk.StringVar(value=app_config.get("proxy_quality"))
        quality_opts = list(app_config.get("format_commands")["Proxies"].keys())
        self.quality_cb = ctk.CTkComboBox(options_frame, variable=self.quality_var, values=quality_opts, state="readonly", font=FONTS["body"], width=200)
        self.quality_cb.pack(side=tk.LEFT)

        buttons_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20))

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

        quality_key = self.quality_var.get()

        app_config.set("proxy_quality", quality_key)

        format_commands = app_config.get("format_commands")
        command_prefix = format_commands["Proxies"].get(quality_key)

        if not command_prefix:
            messagebox.showerror("Error", "Selected format command not found. Please reset settings.")
            return

        format_selector = extract_format_selector(command_prefix)
        if not format_selector:
            messagebox.showerror("Command Error", "Failed to parse selected format command.")
            return

        output_path = str(pathlib.Path(Page.project_location) / "Proxies" / "%(title)s.%(ext)s")
        ydl_opts = {
            "format": format_selector,
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": False
        }
        apply_cookie_option(ydl_opts)

        # Pre-extract info to get the expected filename
        expected_path = None
        try:
            with yt_dlp.YoutubeDL(dict(ydl_opts)) as ydl:
                info = ydl.extract_info(url, download=False)
                # Get the expected filename after yt-dlp processing (merging, etc.)
                expected_path = ydl.prepare_filename(info)
        except Exception:
            # If pre-extraction fails, fall back to template-based path
            pass

        panel = DownloadCard(self.panels_frame, url, ydl_opts, on_finish_callback=self.on_download_complete, post_download_callback=self.convert_to_prores)
        # Store the expected path on the panel for post-download conversion
        if expected_path:
            panel.expected_file = expected_path
        panel.pack(fill=tk.X, padx=15, pady=(0, 10))
        self.active_downloads[panel] = url

    def convert_to_prores(self, panel):
        # Use the pre-calculated expected file path
        expected_path = getattr(panel, 'expected_file', None)
        
        # Fallback: if no expected path, try to find the .mp4 that matches downloaded_files
        if not expected_path:
            media_files = [f for f in panel.downloaded_files if f and os.path.exists(f) and f.lower().endswith('.mp4')]
            if not media_files:
                panel.queue_log("[post] No files found to convert. Skipping ProRes conversion.\n")
                return
        else:
            # Use the expected path if it exists
            if os.path.exists(expected_path):
                media_files = [expected_path]
            else:
                # Fallback: check if there's an .mp4 file in downloaded_files
                media_files = [f for f in panel.downloaded_files if f and os.path.exists(f) and f.lower().endswith('.mp4')]
                if not media_files:
                    panel.queue_log("[post] Expected file not found and no fallback files. Skipping ProRes conversion.\n")
                    return

        panel.after(0, lambda: panel.speed_label.configure(text="Converting to ProRes..."))
        panel.queue_log(f"[post] Converting {len(media_files)} file(s) to ProRes 422...\n")

        for media_path in media_files:
            base, ext = os.path.splitext(media_path)
            output_path = f"{base}.mov"

            # Skip if already converted (output exists)
            if os.path.exists(output_path):
                panel.queue_log(f"[post] Already converted: {os.path.basename(media_path)}\n")
                continue

            ffmpeg_cmd = [
                "ffmpeg", "-i", media_path,
                "-c:v", "prores_ks", "-profile:v", "0", "-vendor", "apl0",
                "-pix_fmt", "yuv422p10le",
                "-c:a", "aac", "-b:a", "128k",
                "-y", output_path
            ]

            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NO_WINDOW

            try:
                panel.queue_log(f"[post] Converting to ProRes 422: {os.path.basename(media_path)}\n")
                proc = subprocess.Popen(
                    ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", creationflags=creation_flags
                )
                for line in iter(proc.stdout.readline, ""):
                    if line.strip():
                        panel.queue_log(line)
                proc.stdout.close()
                returncode = proc.wait()

                if returncode == 0 and os.path.exists(output_path):
                    os.remove(media_path)
                    panel.queue_log(f"[post] Deleted original: {os.path.basename(media_path)}\n")
                else:
                    panel.queue_log(f"[post] ProRes conversion failed, keeping original: {os.path.basename(media_path)}\n")
            except Exception as e:
                panel.queue_log(f"[post] Failed to convert to ProRes: {e}\n")

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
