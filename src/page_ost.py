import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import re
import os
import pathlib

from ui_page import Page, apply_cookie_option
from components import DownloadingPanel
from config import app_config, AUDIO_FORMAT_OPTIONS, AUDIO_BITRATE_OPTIONS
from utils import video_regex
from ui_theme import COLORS, FONTS


class OSTDownloader(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        ctk.CTkLabel(self.frame_content, text="Enter Video/Playlist URL for OST:", font=FONTS["header"], text_color='white').pack(anchor="w", padx=30, pady=(40, 5))

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

        ctk.CTkLabel(options_frame, text="Format:", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 10))
        self.format_var = tk.StringVar(value=app_config.get("ost_format"))
        self.format_cb = ctk.CTkComboBox(options_frame, variable=self.format_var, values=list(AUDIO_FORMAT_OPTIONS.keys()), state="readonly", font=FONTS["body"], width=150, command=self.on_format_change)
        self.format_cb.pack(side=tk.LEFT, padx=(0, 30))

        ctk.CTkLabel(options_frame, text="Bitrate:", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 10))
        self.bitrate_var = tk.StringVar(value=app_config.get("ost_bitrate"))
        self.bitrate_cb = ctk.CTkComboBox(options_frame, variable=self.bitrate_var, values=AUDIO_BITRATE_OPTIONS, state="readonly", font=FONTS["body"], width=150)
        self.bitrate_cb.pack(side=tk.LEFT)

        self.on_format_change(self.format_var.get())

        buttons_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20))

        self.download_button = ctk.CTkButton(
            buttons_frame,
            text="Download OST",
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

        self.panels_frame = ctk.CTkScrollableFrame(self.frame_content, fg_color="transparent", label_text="Active OST Downloads", label_font=FONTS["small"])
        self.panels_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 10))

        self.active_downloads = {}
        return self.frame_content

    def on_format_change(self, selected_format):
        if selected_format == "FLAC":
            self.bitrate_cb.configure(state="disabled")
        else:
            self.bitrate_cb.configure(state="readonly")

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

        ost_format_label = self.format_var.get()
        ost_bitrate = self.bitrate_var.get()
        audio_codec = AUDIO_FORMAT_OPTIONS.get(ost_format_label, "mp3")

        app_config.set("ost_format", ost_format_label)
        app_config.set("ost_bitrate", ost_bitrate)

        output_path = str(pathlib.Path(Page.project_location) / "OST" / "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_codec,
                "preferredquality": ost_bitrate.replace("k", ""),
            }],
            "quiet": True,
            "no_warnings": False
        }
        apply_cookie_option(ydl_opts)

        panel = DownloadingPanel(self.panels_frame, url, ydl_opts, on_finish_callback=self.on_download_complete)
        panel.pack(fill=tk.X, padx=15, pady=(0, 10))
        self.active_downloads[panel] = url

    def on_download_complete(self, panel):
        if panel in self.active_downloads:
            del self.active_downloads[panel]

    def open_downloads_folder(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        target_dir = pathlib.Path(Page.project_location) / "OST"
        target_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(target_dir))
