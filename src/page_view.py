import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import re
import os
import pathlib
from utils import *
from config import app_config, QUALITY_FORMATS

class DownloadingPanel(tk.Frame):
    def __init__(self, master, command, on_finish_callback=None, **kw):
        if 'bg' not in kw:
            kw['bg'] = '#2B2B2B'
        super().__init__(master, **kw)
        self.command = command
        self.on_finish_callback = on_finish_callback
        self.download_process = None

        self.downloading_name = tk.Label(self, text="Starting download...", font=('Poppins', 12, "bold"), fg='white', bg="#2B2B2B")
        self.downloading_name.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.download_progress = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.download_progress.pack(fill=tk.X, padx=20, pady=5)

        # Terminal log output mapping
        self.log_text = tk.Text(self, height=6, bg="#1E1E1E", fg="#A0A0A0", font=('Consolas', 9), relief="flat", highlightthickness=1, highlightbackground='#3E3E42', padx=10, pady=5)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 5))
        self.log_text.configure(state='disabled')

        bottom_frame = tk.Frame(self, bg='#2B2B2B')
        bottom_frame.pack(fill=tk.X, padx=20, pady=(5, 15))

        self.speed_display = tk.Label(bottom_frame, text='Download Speed: N/A', font=('Poppins', 10), fg='#B3B3B3', bg="#2B2B2B")
        self.speed_display.pack(side=tk.LEFT)

        self.stop_button = tk.Button(bottom_frame, text="Cancel", font=("Poppins", 10, "bold"), fg="white", bg='#DC143C', activebackground='#A60F2D', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.stop_download)
        self.stop_button.pack(side=tk.RIGHT, ipadx=15, ipady=4)
        change_on_hover(self.stop_button, '#FF1E4D' ,'#DC143C')

        self.download_thread = threading.Thread(target=self.start_download, daemon=True)
        self.download_thread.start()

    def start_download(self):
        try:
            # Hide console window explicitly on Windows
            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NO_WINDOW

            self.download_process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags
            )

            file_regex = re.compile(r'\[download\] Destination: .*[\/\\](.+)')
            progress_regex = re.compile(r'(\d+\.\d+)%.*at\s+([\d\w\./s]+)')
            
            for line in self.download_process.stdout:
                # Log to terminal trace viewer
                self.after(0, lambda l=line: self.append_log(l))

                file_match = file_regex.search(line)
                if file_match:
                    file_name = file_match.group(1)
                    self.after(0, lambda n=file_name: self.downloading_name.config(text=n))

                progress_match = progress_regex.search(line)
                if progress_match:
                    percentage = float(progress_match.group(1))
                    speed = progress_match.group(2)
                    self.after(0, lambda p=percentage, s=speed: self.update_progress(p, s))

            self.download_process.wait()
            
            if self.download_process.returncode == 0:
                self.after(0, self.on_finish)
                
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Download Error", str(err)))
            self.after(0, self.stop_download)

    def on_finish(self):
        messagebox.showinfo("Download Completed!", "Video files have been successfully downloaded.")
        self.stop_download()

    def append_log(self, text):
        if not self.winfo_exists():
            return
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def stop_download(self):
        if self.download_process and self.download_process.poll() is None: 
            self.download_process.kill()
            
        if self.on_finish_callback:
            self.on_finish_callback(self)
            
        self.destroy()

    def update_progress(self, percentage, speed):
        if not self.winfo_exists():
            return
        self.download_progress['value'] = percentage
        self.speed_display.config(text=f'Download Speed: {speed}')

class Page(tk.Frame):
    project_location = ""
    def __init__(self, master, **kw):
        if 'bg' not in kw and 'background' not in kw:
            kw['bg'] = '#1A1A1D'
        super().__init__(master, **kw)

class TranscriptGenerator(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> tk.Frame:
        """
        Create the widgets specific to this service (TranscriptGenerator)

        """

        self.frame_content = tk.Frame(self, bg='#1A1A1D')

        # url location
        tk.Label(self.frame_content, text="Enter Video Link:", font=("Poppins", 16, "bold"), fg='white', bg="#1A1A1D").pack(anchor="w", padx=30, pady=(40, 5))
        self.url_box = tk.Entry(self.frame_content, bg='#2B2B2B', fg='white', insertbackground='white', relief='flat', font=('Poppins', 12), highlightthickness=1, highlightbackground='#3E3E42', highlightcolor='#DC143C')
        self.url_box.pack(fill=tk.X, padx=30, pady=(0, 20), ipady=8)

        # transcript button
        self.btn_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        self.btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        self.transcript_button = tk.Button(self.btn_frame, text="Transcript It", font=("Poppins", 12, "bold"), fg="white", bg='#DC143C', activebackground='#A60F2D', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.generate)
        self.transcript_button.pack(side=tk.LEFT, ipady=8, ipadx=40)
        change_on_hover(self.transcript_button, '#FF1E4D', '#DC143C')
        
        self.status_label = tk.Label(self.btn_frame, text="", font=("Poppins", 11), fg="#AAAAAA", bg="#1A1A1D")
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Output Text Box
        self.text_box = tk.Text(self.frame_content, bg='#2B2B2B', fg='white', font=('Poppins', 12), relief='flat', highlightthickness=1, highlightbackground='#3E3E42', insertbackground='white', state=tk.DISABLED)
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

        self.transcript_button.config(state=tk.DISABLED, bg="#888888")
        self.status_label.config(text="Fetching transcript...")
        self.text_box.config(state=tk.NORMAL)
        self.text_box.delete("1.0", tk.END)
        self.text_box.config(state=tk.DISABLED)

        import threading
        t = threading.Thread(target=self.fetch_and_process, args=(url,))
        t.daemon = True
        t.start()

    def fetch_and_process(self, url):
        import subprocess
        import glob
        import re
        
        script_dir = pathlib.Path(Page.project_location) / "Script"
        script_dir.mkdir(parents=True, exist_ok=True)
        
        # Temp vtt file
        temp_out = script_dir / "temp_transcript"
        
        # We target auto-subs first, or regular subs if available
        cmd = [
            'yt-dlp', '--write-auto-subs', '--write-subs', '--sub-langs', 'en.*',
            '--skip-download', '-o', str(temp_out) + ".%(ext)s", url
        ]
        
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
            
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
        process.wait()

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
        self.transcript_button.config(state=tk.NORMAL, bg="#DC143C")
        self.status_label.config(text="")
        messagebox.showerror("Error", message)

    def on_success(self, text, path):
        if not self.winfo_exists():
            return
        self.transcript_button.config(state=tk.NORMAL, bg="#DC143C")
        self.status_label.config(text="Success!")
        
        self.text_box.config(state=tk.NORMAL)
        self.text_box.insert("1.0", text)
        self.text_box.config(state=tk.DISABLED)
        
        try:
            os.startfile(str(path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file automatically: {e}")
        


class ClipsDownloader(Page):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.create_frame_content().pack(fill=tk.BOTH, expand=True)

    def create_frame_content(self) -> tk.Frame:
        """
        Create the widgets specific to this service (Clips Downloader)

        """

        self.frame_content = tk.Frame(self, bg='#1A1A1D')

        #url location
        tk.Label(self.frame_content, text="Enter Video/Playlist URL for Clips:", font=("Poppins", 16, "bold"), fg='white', bg="#1A1A1D").pack(anchor="w", padx=30, pady=(40, 5))
        self.url_box = tk.Entry(self.frame_content, bg='#2B2B2B', fg='white', insertbackground='white', relief='flat', font=('Poppins', 12), highlightthickness=1, highlightbackground='#3E3E42', highlightcolor='#DC143C')
        self.url_box.pack(fill=tk.X, padx=30, pady=(0, 20), ipady=8)

        #buttons frame
        buttons_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        buttons_frame.pack(pady=(0, 20))

        #download button
        self.download_button = tk.Button(buttons_frame, text="Download Clips", font=("Poppins", 12, "bold"), fg="white", bg='#DC143C', activebackground='#A60F2D', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.download)
        self.download_button.pack(side=tk.LEFT, padx=(0, 15), ipady=8, ipadx=30)
        change_on_hover(self.download_button, '#FF1E4D' ,'#DC143C')

        #show downloads button
        self.show_dir_button = tk.Button(buttons_frame, text="Show Downloads", font=("Poppins", 12, "bold"), fg="white", bg='#3E3E42', activebackground='#4A4A4F', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.open_downloads_folder)
        self.show_dir_button.pack(side=tk.LEFT, ipady=8, ipadx=20)
        change_on_hover(self.show_dir_button, '#4A4A4F', '#3E3E42')

        self.panels_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        self.panels_frame.pack(fill=tk.BOTH, expand=True)

        self.active_downloads = {}
        return self.frame_content

    def download(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        url = str(self.url_box.get()).strip()
        if re.match(youtube_regex, url) is None:
            messagebox.showerror('Invalid Link', "Please enter a valid youtube video/playlist url")
            return

        if url in self.active_downloads.values():
            messagebox.showwarning('Duplicate Download', "This URL is already being downloaded!")
            return

        if len(self.active_downloads) >= 2:
            messagebox.showwarning('Limit Reached', "You can only run a maximum of 2 downloads at a time.")
            return

        quality_key = app_config.get("clips_quality")
        quality_str = QUALITY_FORMATS["Clips"].get(quality_key, QUALITY_FORMATS["Clips"]["Best Available"])

        command = ['yt-dlp',  '-f',  quality_str,  '-o', str(pathlib.Path(Page.project_location) / "Clips" / "%(title)s.%(ext)s"), url]
        
        panel = DownloadingPanel(self.panels_frame, command, on_finish_callback=self.on_download_complete)
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

    def create_frame_content(self) -> tk.Frame:
        """
        Create the widgets specific to this service (Proxy Downloader)

        """

        self.frame_content = tk.Frame(self, bg='#1A1A1D')

        #url location
        tk.Label(self.frame_content, text="Enter Video/Playlist URL for Proxy:", font=("Poppins", 16, "bold"), fg='white', bg="#1A1A1D").pack(anchor="w", padx=30, pady=(40, 5))
        self.url_box = tk.Entry(self.frame_content, bg='#2B2B2B', fg='white', insertbackground='white', relief='flat', font=('Poppins', 12), highlightthickness=1, highlightbackground='#3E3E42', highlightcolor='#DC143C')
        self.url_box.pack(fill=tk.X, padx=30, pady=(0, 20), ipady=8)

        #buttons frame
        buttons_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        buttons_frame.pack(pady=(0, 20))

        #download button
        self.download_button = tk.Button(buttons_frame, text="Download Proxy", font=("Poppins", 12, "bold"), fg="white", bg='#DC143C', activebackground='#A60F2D', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.download)
        self.download_button.pack(side=tk.LEFT, padx=(0, 15), ipady=8, ipadx=30)
        change_on_hover(self.download_button, '#FF1E4D' ,'#DC143C')

        #show downloads button
        self.show_dir_button = tk.Button(buttons_frame, text="Show Downloads", font=("Poppins", 12, "bold"), fg="white", bg='#3E3E42', activebackground='#4A4A4F', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.open_downloads_folder)
        self.show_dir_button.pack(side=tk.LEFT, ipady=8, ipadx=20)
        change_on_hover(self.show_dir_button, '#4A4A4F', '#3E3E42')

        self.panels_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        self.panels_frame.pack(fill=tk.BOTH, expand=True)

        self.active_downloads = {}
        return self.frame_content

    def download(self):
        if not Page.project_location:
            messagebox.showerror("Error", "Please select a Project Folder location in the Home menu first.")
            return

        url = str(self.url_box.get()).strip()
        if re.match(youtube_regex, url) is None:
            messagebox.showerror('Invalid Link', "Please enter a valid youtube video/playlist url")
            return

        if url in self.active_downloads.values():
            messagebox.showwarning('Duplicate Download', "This URL is already being downloaded!")
            return

        if len(self.active_downloads) >= 2:
            messagebox.showwarning('Limit Reached', "You can only run a maximum of 2 downloads at a time.")
            return

        quality_key = app_config.get("proxy_quality")
        quality_str = QUALITY_FORMATS["Proxies"].get(quality_key, QUALITY_FORMATS["Proxies"]["360p"])

        command = ['yt-dlp',  '-f',  quality_str, "--recode-video", "mp4",  '-o', str(pathlib.Path(Page.project_location) / "Proxies" / "%(title)s.%(ext)s"), url]
        
        panel = DownloadingPanel(self.panels_frame, command, on_finish_callback=self.on_download_complete)
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

    def create_frame_content(self) -> tk.Frame:
        self.frame_content = tk.Frame(self, bg='#1A1A1D')

        #project folder location entry
        tk.Label(self.frame_content, text="Project Folder Location:", font=("Poppins", 16, "bold"), fg='white', bg="#1A1A1D").pack(anchor="w", padx=30, pady=(40, 5))
        
        # Frame for entry and button
        location_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        location_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        self.project_location_entry = tk.Entry(location_frame, bg='#2B2B2B', fg='white', disabledbackground='#2D2D30', disabledforeground='#888888', insertbackground='white', relief='flat', font=('Poppins', 12), highlightthickness=1, highlightbackground='#3E3E42', highlightcolor='#DC143C')
        self.project_location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        
        saved_folder = app_config.get("project_folder")
        if saved_folder:
            Page.project_location = saved_folder
            self.project_location_entry.insert(0, saved_folder)
            
        self.project_location_entry.configure(state='disabled')

        # The change button to change project folder location
        self.select_button = tk.Button(location_frame, text='Select', command=self.select_project_folder, font=("Poppins", 10, "bold"), fg="white", bg='#DC143C', activebackground='#A60F2D', activeforeground='white', cursor="hand2", bd=0, relief="flat")
        self.select_button.pack(side=tk.LEFT, ipady=8, ipadx=15)
        change_on_hover(self.select_button, '#FF1E4D', "#DC143C")

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

    def create_frame_content(self) -> tk.Frame:
        self.frame_content = tk.Frame(self, bg='#1A1A1D')

        # Title
        tk.Label(self.frame_content, text="Application Settings", font=("Poppins", 16, "bold"), fg='white', bg="#1A1A1D").pack(anchor="w", padx=30, pady=(40, 20))

        # Proxy Quality
        proxy_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        proxy_frame.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(proxy_frame, text="Proxy Quality: ", font=("Poppins", 12), fg='white', bg="#1A1A1D").pack(side=tk.LEFT, padx=(0, 20))
        
        self.proxy_var = tk.StringVar(value=app_config.get("proxy_quality"))
        proxy_opts = list(QUALITY_FORMATS["Proxies"].keys())
        self.proxy_cb = ttk.Combobox(proxy_frame, textvariable=self.proxy_var, values=proxy_opts, state="readonly", font=("Poppins", 11), width=25)
        self.proxy_cb.pack(side=tk.LEFT)

        # Clips Quality
        clips_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        clips_frame.pack(fill=tk.X, padx=30, pady=10)

        tk.Label(clips_frame, text="Clips Quality: ", font=("Poppins", 12), fg='white', bg="#1A1A1D").pack(side=tk.LEFT, padx=(0, 20))

        self.clips_var = tk.StringVar(value=app_config.get("clips_quality"))
        clips_opts = list(QUALITY_FORMATS["Clips"].keys())
        self.clips_cb = ttk.Combobox(clips_frame, textvariable=self.clips_var, values=clips_opts, state="readonly", font=("Poppins", 11), width=25)
        self.clips_cb.pack(side=tk.LEFT)

        # Buttons
        buttons_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        buttons_frame.pack(fill=tk.X, padx=30, pady=40)

        self.save_button = tk.Button(buttons_frame, text="Save Settings", font=("Poppins", 11, "bold"), fg="white", bg='#DC143C', activebackground='#A60F2D', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.save_settings)
        self.save_button.pack(side=tk.LEFT, ipady=6, ipadx=20)
        change_on_hover(self.save_button, '#FF1E4D', '#DC143C')

        self.reset_button = tk.Button(buttons_frame, text="Reset Defaults", font=("Poppins", 11, "bold"), fg="white", bg='#3E3E42', activebackground='#4A4A4F', activeforeground='white', relief="flat", bd=0, cursor="hand2", command=self.reset_settings)
        self.reset_button.pack(side=tk.LEFT, padx=20, ipady=6, ipadx=20)
        change_on_hover(self.reset_button, '#4A4A4F', '#3E3E42')

        return self.frame_content

    def save_settings(self):
        app_config.set("proxy_quality", self.proxy_var.get())
        app_config.set("clips_quality", self.clips_var.get())
        messagebox.showinfo("Success", "Settings have been safely updated.")

    def reset_settings(self):
        self.proxy_var.set("360p")
        self.clips_var.set("Best Available")
        app_config.set("proxy_quality", "360p")
        app_config.set("clips_quality", "Best Available")
        messagebox.showinfo("Reset", "Settings have been reverted to defaults.")