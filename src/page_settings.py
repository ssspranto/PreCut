import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os

from ui_page import Page
from config import app_config
from utils import get_available_js_runtimes
from ui_theme import COLORS, FONTS


class Settings(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        ctk.CTkLabel(self.frame_content, text="Application Settings", font=FONTS["title"], text_color='white').pack(anchor="w", padx=30, pady=(40, 20))

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

        if self.js_runtime_var.get() not in self.available_runtimes and self.available_runtimes:
            self.js_runtime_var.set(self.available_runtimes[0])

        self.js_runtime_cb = ctk.CTkComboBox(ejs_frame, variable=self.js_runtime_var, values=self.available_runtimes if self.available_runtimes else ["None Found"], state="readonly", font=FONTS["body"], width=150)
        self.js_runtime_cb.pack(side=tk.LEFT, padx=10)

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

        app_config.set("use_cookies", use_cookies)
        app_config.set("cookie_file", cookie_file)
        app_config.set("use_ejs", use_ejs)
        app_config.set("js_runtime", js_runtime)

        messagebox.showinfo("Success", "Settings have been safely updated.")

    def reset_settings(self):
        app_config.set("clips_quality", "Best Available")
        app_config.set("proxy_quality", "360p")
        app_config.set("clips_codec", "H.264 (Compatible)")
        app_config.set("proxy_codec", "H.264 (Compatible)")
        app_config.set("ost_format", "MP3")
        app_config.set("ost_bitrate", "192k")
        app_config.set("transcript_format", "Plain Text (.txt)")
        app_config.set("use_cookies", False)
        app_config.set("cookie_file", "")
        app_config.set("use_ejs", True)
        app_config.set("js_runtime", "deno")

        app_config.regenerate_all_commands()

        self.use_cookies_var.set(False)
        self.cookie_file_var.set("")
        self.on_cookies_toggle()
        self.use_ejs_var.set(True)
        self.js_runtime_var.set("deno")
        self.on_ejs_toggle()

        messagebox.showinfo("Reset", "All settings have been reverted to defaults.")
