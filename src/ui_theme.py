import customtkinter as ctk

# PreCut 2.0 Color Palette
COLORS = {
    "bg_dark": "#0B0B0C",      # Deep Obsidian
    "bg_charcoal": "#121212",  # Sidebar/Header
    "bg_card": "#1A1A1D",      # Content Cards
    "accent_crimson": "#DC143C", # Signature Crimson
    "accent_glow": "#FF1E4D",    # Hover Glow
    "text_main": "#FFFFFF",
    "text_dim": "#888888",
    "border": "#2B2B2B"
}

# Typography
FONTS = {
    "title": ("Poppins", 24, "bold"),
    "header": ("Poppins", 16, "bold"),  # Matches old label size (16)
    "body": ("Inter", 14),              # Matches old input/treeview size (14)
    "body_bold": ("Inter", 14, "bold"),
    "small": ("Inter", 12)
}

def setup_theme():
    """Initialize CustomTkinter appearance settings"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue") # We will use custom colors for widgets
