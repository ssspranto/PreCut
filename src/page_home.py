import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

from ui_page import Page
from config import app_config
from ui_theme import COLORS, FONTS


class Home(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> ctk.CTkFrame:
        self.frame_content = ctk.CTkFrame(self, fg_color="transparent")

        ctk.CTkLabel(self.frame_content, text="Project Folder Location:", font=FONTS["header"], text_color='white').pack(anchor="w", padx=30, pady=(40, 5))

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
