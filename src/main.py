import sys
import os

# Redirect pycache folder globally to the local data directory
pycache_dir = os.path.join(get_data_dir(), 'pycache')
os.makedirs(pycache_dir, exist_ok=True)
sys.pycache_prefix = pycache_dir

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from page_home import Home
from page_transcript import TranscriptGenerator
from page_clips import ClipsDownloader
from page_proxy import ProxyDownloader
from page_ost import OSTDownloader
from page_settings import Settings
from PIL import Image, ImageTk
from utils import check_dependencies, get_asset_path, get_data_dir
from ui_theme import COLORS, FONTS, setup_theme

class ServicesView(ctk.CTkFrame):
    def __init__(self, master, **kw):
        if 'fg_color' not in kw:
            kw['fg_color'] = COLORS["bg_dark"]
        super().__init__(master, **kw)

        # Key: service name (i.e: 'Script Maker  or 'Clips Downloader')
        # Value: Page object (derived from ttk.Frame)
        self.pages = {}

        # Give row 0 and column 1 as much room as it needs
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.create_frame_treeview().grid(row=0, column=0, sticky="ens")

        self.create_frame_page().grid(row=0, column=1, sticky="nsew")

        # Base home page mapped to our Heading
        h = Home(self.frame_page)
        self.pages['Home'] = h
        h.place(relx=0, rely=0, relwidth=1, relheight=1)

    def create_frame_page(self) -> ctk.CTkFrame:
        '''
        Create the frame that'll show the current service page
        '''
        self.frame_page = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=15)
        return self.frame_page

    def create_frame_treeview(self) -> ctk.CTkFrame: 
        """
        Create the frame that will hold the modern Sidebar.
        """
        self.frame_treeview = ctk.CTkFrame(self, fg_color=COLORS["bg_charcoal"], corner_radius=0, width=280)
        self.frame_treeview.pack_propagate(False)

        self.sidebar = Sidebar(self.frame_treeview, on_navigate=self.show_page)
        self.sidebar.pack(fill=tk.BOTH, expand=True)

        return self.frame_treeview
    
    def on_treeview_selection_changed(self, event):
        # Deprecated for new sidebar
        pass

    def on_treeview_click(self, event):
        # Deprecated for new sidebar
        pass

        """
        Handle heading clicks since they do not trigger <<TreeviewSelect>> natively
        """
        region = self.treeview_services.identify_region(event.x, event.y)
        if region == "heading":
            # Remove regular item selection highlight physically
            if self.treeview_services.selection():
                self.treeview_services.selection_remove(self.treeview_services.selection())
            # Load the home menu / generic handler
            self.show_page('Home')
    

    def on_treeview_selection_changed(self, event):
        """
        Switch to the frame related to the newly selected service
        """
        
        selected_items = self.treeview_services.selection()
        
        # If selection was just cleared programmatically, do nothing
        if not selected_items:
            return
            
        pass

    def show_page(self, service_name: str):
        '''
        Show the page associated with the service_name
        '''
        page = self.pages.get(service_name)
        if page:
            page.tkraise()
            self.sidebar.select_item(service_name)

    def add_page(self, image_path: str, service_name: str, page):
        '''
        Instantiate a page frame and add it to the pages dictionary
        '''
        
        # Load the image and convert it to a CTkImage
        try:
            pil_img = Image.open(image_path)
            ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(20, 20))
        except Exception:
            # Fallback if icon is missing
            pil_img = Image.new("RGBA", (20, 20), (0,0,0,0))
            ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(20, 20))
        
        # Instantiate page
        p = page(self.frame_page)
        self.pages[service_name] = p
        
        # Pack it immediately so it's ready for tkraise()
        p.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Keep a reference
        self.pages[service_name].image = ctk_image

        # Add the button to the sidebar
        self.sidebar.add_item(text=service_name, image=ctk_image)


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.on_navigate = on_navigate
        self.buttons = {}

        # Logo / Title
        self.logo_label = ctk.CTkLabel(self, text="PRECUT 2.1", font=FONTS["title"], text_color=COLORS["accent_crimson"])
        self.logo_label.pack(pady=(40, 40), padx=20)

        # Home button (fixed)
        self.add_item("Home", None) # Home usually doesn't have an icon in the same way or uses a default

    def add_item(self, text, image):
        if text in self.buttons:
            return
            
        btn = ctk.CTkButton(
            self,
            text=text,
            image=image,
            compound="left",
            font=FONTS["header"] if text == "Home" else FONTS["body_bold"],
            fg_color="transparent",
            text_color=COLORS["text_main"],
            hover_color=COLORS["bg_card"],
            anchor="w",
            corner_radius=8,
            height=45,
            command=lambda: self.on_navigate(text)
        )
        btn.pack(fill=tk.X, padx=15, pady=5)
        self.buttons[text] = btn

    def select_item(self, text):
        for name, btn in self.buttons.items():
            if name == text:
                btn.configure(fg_color=COLORS["accent_crimson"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_main"])


if __name__ == "__main__":
    setup_theme()
    
    root = ctk.CTk()
    root.title("PreCut 2.1 - Content Workflow Suite")
    root.geometry('1100x750+450+150')
    root.configure(fg_color=COLORS["bg_dark"])

    # Dependency Check
    missing_tools = check_dependencies()
    if missing_tools:
        messagebox.showwarning(
            "Missing Dependencies",
            f"The following required tools were not found in your PATH:\n\n"
            f"{', '.join(missing_tools)}\n\n"
            "High-quality video merging and certain downloads may fail. "
            "Please ensure they are installed and added to your system environment variables."
        )

    # App Icon
    try:
        # icon_pil = Image.open(get_asset_path('assets/precut.png'))
        # icon_photo = ImageTk.PhotoImage(icon_pil)
        root.iconbitmap(get_asset_path('assets/precut.ico'))
    except Exception as e:
        print(f"Icon loading error: {e}")
    
    services = ServicesView(root)

    services.add_page(image_path=get_asset_path('assets/transcript_generator.png'), service_name='Transcript Generator', page=TranscriptGenerator)
    services.add_page(image_path=get_asset_path('assets/clips_downloader.png'), service_name='Clip Downloader', page=ClipsDownloader)
    services.add_page(image_path=get_asset_path('assets/proxy_downloader.png'), service_name='Proxy Downloader', page=ProxyDownloader)
    services.add_page(image_path=get_asset_path('assets/ost_downloader.png'), service_name='OST Downloader', page=OSTDownloader)
    services.add_page(image_path=get_asset_path('assets/settings.png'), service_name='Settings', page=Settings)

    # Initialize app with the Home page displayed
    services.show_page('Home')

    services.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()