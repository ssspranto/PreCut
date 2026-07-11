import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import re
import os
import pathlib
import glob

import yt_dlp

from ui_page import Page, apply_cookie_option
from config import app_config, TEXT_FORMAT_OPTIONS
from ui_theme import COLORS, FONTS


class TranscriptGenerator(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

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

        options_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        options_frame.pack(anchor="w", padx=30, pady=(0, 20))

        ctk.CTkLabel(options_frame, text="Text Format:", font=FONTS["body_bold"], text_color='white').pack(side=tk.LEFT, padx=(0, 10))
        self.format_var = tk.StringVar(value=app_config.get("transcript_format"))
        self.format_cb = ctk.CTkComboBox(options_frame, variable=self.format_var, values=list(TEXT_FORMAT_OPTIONS.keys()), state="readonly", font=FONTS["body"], width=200)
        self.format_cb.pack(side=tk.LEFT)

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

        app_config.set("transcript_format", self.format_var.get())

        self.transcript_button.configure(state="disabled", fg_color="#888888")
        self.status_label.configure(text="Fetching transcript...")
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", tk.END)
        self.text_box.configure(state="disabled")

        t = threading.Thread(target=self.fetch_and_process, args=(url,))
        t.daemon = True
        t.start()

    def fetch_and_process(self, url):
        script_dir = pathlib.Path(Page.project_location) / "Script"
        script_dir.mkdir(parents=True, exist_ok=True)

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

        vtt_files = glob.glob(str(script_dir / "temp_transcript*.vtt"))

        if not vtt_files:
            self.after(0, lambda: self.on_error("Failed to fetch transcript (no subtitles found)."))
            return

        try:
            with open(vtt_files[0], "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.after(0, lambda: self.on_error(f"Failed to read vtt file: {e}"))
            return

        for f in vtt_files:
            try:
                os.remove(f)
            except:
                pass

        content = re.sub(r"^WEBVTT.*?\n", "", content, flags=re.MULTILINE | re.DOTALL)
        content = re.sub(r"Kind: captions\nLanguage: en.*?\n", "", content, flags=re.MULTILINE | re.IGNORECASE)
        content = re.sub(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}.*?\n", "", content, flags=re.MULTILINE)
        content = re.sub(r"<[^>]+>", "", content)

        lines = content.split('\n')
        clean_words = []
        for line in lines:
            line = line.strip()
            if not line or line.isdigit():
                continue
            if clean_words and clean_words[-1] == line:
                continue
            clean_words.append(line)

        final_script = " ".join(clean_words).replace('\n', ' ').replace('\r', ' ')

        format_label = app_config.get("transcript_format")
        ext = TEXT_FORMAT_OPTIONS.get(format_label, "txt")
        final_path = script_dir / f"script.{ext}"
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
