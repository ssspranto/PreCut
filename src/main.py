import sys
import os

# Redirect pycache folder globally to Documents
pycache_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'PreCut', 'data', 'pycache')
os.makedirs(pycache_dir, exist_ok=True)
sys.pycache_prefix = pycache_dir

import tkinter as tk
from tkinter import ttk
from page_view import TranscriptGenerator, ClipsDownloader, ProxyDownloader, Home, Settings
from PIL import Image, ImageTk

class ServicesView(tk.Frame):
    def __init__(self, master, **kw):
        if 'bg' not in kw and 'background' not in kw:
            kw['bg'] = '#121212'
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
        self.pages['Home'] = Home(self.frame_page)

    def create_frame_page(self) -> tk.Frame:
        '''
        Create the frame that'll show the current service page
        '''

        self.frame_page = tk.Frame(self, bg='#1A1A1D', bd=0)

        return self.frame_page

    def create_frame_treeview(self) -> tk.Frame: 
        """
        Create the frame that will hold all the services treeview widget 
        and also instantiate the ServicesTreeView class.
        """

        self.frame_treeview = tk.Frame(self, bg='#121212', bd=0)

        self.treeview_services = ServicesTreeView(self.frame_treeview)
        self.treeview_services.bind("<<TreeviewSelect>>", self.on_treeview_selection_changed)
        self.treeview_services.bind("<Button-1>", self.on_treeview_click)
        self.treeview_services.pack(fill=tk.BOTH, expand=True)

        return self.frame_treeview
    
    def on_treeview_click(self, event):
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
            
        service_name = self.treeview_services.item(selected_items[0]).get("text")

        self.show_page(service_name)

    def show_page(self, service_name: str):
        '''
        pack_forget() all pages and pack the given page name
        '''

        # Dynamically highlight the heading if we are on the Home page
        style = ttk.Style()
        if service_name == 'Home':
            style.configure("Services.Treeview.Heading", background="#DC143C", foreground="white")
            style.map("Services.Treeview.Heading", background=[('active', '#FF1E4D')], foreground=[('active', 'white')])
        else:
            style.configure("Services.Treeview.Heading", background="#121212", foreground="#FFFFFF")
            style.map("Services.Treeview.Heading", background=[('active', '#1A1A1D')], foreground=[('active', '#DC143C')])

        for page_name in self.pages.keys():
            self.pages[page_name].pack_forget()

        self.pages[service_name].pack(fill=tk.BOTH, expand=True)

    def add_page(self, image_path: str, service_name: str, page):
        '''
        Instantiate a page frame and add it to the pages dictionary

        image_path: a path to an image file
        service_name: name of the service
        page: a Page class object
        '''

        # Load the image and convert it to a photo image
        try:
            with Image.open(image_path) as img:
                # Resize the image so it fits nicely as an icon (e.g. 32x32 pixels)
                img = img.resize((18, 18))
                # Convert it to a photo image
                photo_image = ImageTk.PhotoImage(img)
        except Exception:
            # Fallback if icon is missing
            img = Image.new("RGBA", (18, 18), (0,0,0,0))
            photo_image = ImageTk.PhotoImage(img)
        
        # Add page to dictionary so we can show it when needed
        self.pages[service_name] = page(self.frame_page)

        # Keep a reference to the image so that it doesn't get garbage collected.
        self.pages[service_name].image = photo_image

        # Insert the service name into the service treeview.set
        self.treeview_services.add_service(image=photo_image, section_text=service_name)


class ServicesTreeView(ttk.Treeview):
    def __init__(self, master, **kw):
        
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure the style for the treeview
        style.configure(
            "Services.Treeview", 
            background="#121212", 
            fieldbackground="#121212", 
            foreground="#E0E0E0", 
            borderwidth=0,
            bordercolor="#121212",
            lightcolor="#121212",
            darkcolor="#121212",
            font=('Poppins', 14),
            rowheight=45
        )
        
        # Configure selection color (matches the red brand color)
        style.map(
            "Services.Treeview", 
            background=[('selected', '#DC143C')]
        )
        
        style.configure(
            "Services.Treeview.Heading",
            background="#121212",
            foreground="#FFFFFF",
            borderwidth=0,
            bordercolor="#121212",
            lightcolor="#121212",
            darkcolor="#121212",
            font=('Poppins', 14, 'bold')
        )

        style.map(
            "Services.Treeview.Heading",
            background=[('active', '#1A1A1D')],
            foreground=[('active', '#DC143C')]
        )
        
        kw['style'] = "Services.Treeview"
        
        super().__init__(master, **kw)

        self.heading("#0", text="Home")
        self.column("#0", width=290, minwidth=250)

    def add_service(self, image, section_text: str):
        '''
        Insert a row
        '''

        self.insert(parent="", index=tk.END, image=image, text=section_text)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("PreCut - Content Workflow Helper")
    root.geometry('1024x720+450+150')
    root.configure(bg="#1A1A1D")

    # App Icon
    try:
        icon_img = Image.open('assets/precut.png')
        icon_photo = ImageTk.PhotoImage(icon_img)
        root.iconphoto(True, icon_photo)
    except Exception as e:
        print(f"Icon loading error: {e}")
    
    services = ServicesView(root, relief="flat")

    services.add_page(image_path='assets/transcript_generator.png', service_name='Transcript Generator', page=TranscriptGenerator)

    services.add_page(image_path='assets/clips_downloader.png', service_name='Clip Downloader', page=ClipsDownloader)

    services.add_page(image_path='assets/proxy_downloader.png', service_name='Proxy Downloader', page=ProxyDownloader)

    services.add_page(image_path='assets/settings.png', service_name='Settings', page=Settings)

    # Initialize app with the Home page displayed
    services.show_page('Home')

    services.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()