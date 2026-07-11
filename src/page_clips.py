import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import re
import os
import pathlib

from ui_page import Page, apply_cookie_option, extract_format_selector
from components import DownloadCard
from config import app_config, CODEC_OPTIONS
from utils import video_regex
from ui_theme import COLORS, FONTS


class ClipsDownloader(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

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

        options_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        options_frame.pack(anchor="w", padx=30, pady=(0, 20))

        ctk.CTkLabel(options_frame, text="Quality:", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 10))
        self.quality_var = tk.StringVar(value=app_config.get("clips_quality"))
        quality_opts = list(app_config.get("format_commands")["Clips"].keys())
        self.quality_cb = ctk.CTkComboBox(options_frame, variable=self.quality_var, values=quality_opts, state="readonly", font=FONTS["body"], width=200)
        self.quality_cb.pack(side=tk.LEFT, padx=(0, 30))

        ctk.CTkLabel(options_frame, text="Codec:", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 10))
        self.codec_var = tk.StringVar(value=app_config.get("clips_codec"))
        self.codec_cb = ctk.CTkComboBox(options_frame, variable=self.codec_var, values=list(CODEC_OPTIONS.keys()), state="readonly", font=FONTS["body"], width=200)
        self.codec_cb.pack(side=tk.LEFT)

        buttons_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20))

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

        quality_key = self.quality_var.get()
        new_codec = self.codec_var.get()
        old_codec = app_config.get("clips_codec")

        app_config.set("clips_quality", quality_key)
        app_config.set("clips_codec", new_codec)

        if old_codec != new_codec:
            app_config.regenerate_commands("Clips")

        format_commands = app_config.get("format_commands")
        command_prefix = format_commands["Clips"].get(quality_key)

        if not command_prefix:
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
        panel.pack(fill=tk.X, padx=15, pady=(0, 10))
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
