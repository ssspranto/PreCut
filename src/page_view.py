import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import re
import os
import pathlib
import shlex
import glob
import yt_dlp
from utils import *
from config import app_config, CODEC_OPTIONS

class DownloadCancelled(Exception):
    pass

def apply_cookie_option(ydl_opts):
    # Disable color codes to keep UI text clean
    ydl_opts["no_color"] = True
    
    # Apply Cookie settings
    use_cookies = bool(app_config.get("use_cookies"))
    cookie_file = str(app_config.get("cookie_file") or "").strip()
    if use_cookies and cookie_file:
        ydl_opts["cookiefile"] = os.path.normpath(cookie_file).replace("\\", "/")

    # Apply EJS (External JS) settings to solve JS challenges
    if bool(app_config.get("use_ejs")):
        ydl_opts["remote_components"] = ["ejs:github"]
        runtime = app_config.get("js_runtime")
        if runtime:
            # The API expects a dict of {runtime_name: config_dict}
            ydl_opts["js_runtimes"] = {runtime: {}}

def extract_format_selector(command_prefix):
    parts = shlex.split(command_prefix)
    for idx, part in enumerate(parts):
        if part in ("-f", "--format") and idx + 1 < len(parts):
            return parts[idx + 1]
    return None

class YdlPanelLogger:
    def __init__(self, panel):
        self.panel = panel

    def debug(self, msg):
        self.panel.queue_log(f"{msg}\n")

    def warning(self, msg):
        self.panel.queue_log(f"WARNING: {msg}\n")

    def error(self, msg):
        self.panel.queue_log(f"ERROR: {msg}\n")

class DownloadingPanel(tk.Frame):
    def __init__(self, master, url, ydl_opts, on_finish_callback=None, **kw):
        if 'bg' not in kw:
            kw['bg'] = '#2B2B2B'
        super().__init__(master, **kw)
        self.url = url
        self.ydl_opts = dict(ydl_opts)
        self.on_finish_callback = on_finish_callback
        self.cancel_requested = False
        self._closed = False
        self.downloaded_files = []

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
            runtime_opts = dict(self.ydl_opts)
            runtime_opts["logger"] = YdlPanelLogger(self)
            runtime_opts["progress_hooks"] = [self.on_progress_update]
            with yt_dlp.YoutubeDL(runtime_opts) as ydl:
                ydl.download([self.url])

            if self.cancel_requested:
                self.queue_log("[download] Cancelled by user.\n")
                self.after(0, self._close_panel)
                return

            self.normalize_downloaded_audio()
            self.after(0, self.on_finish)
        except DownloadCancelled:
            self.queue_log("[download] Cancelled by user.\n")
            self.after(0, self._close_panel)
        except yt_dlp.utils.DownloadError as e:
            if not self.cancel_requested:
                self.after(0, lambda err=e: messagebox.showerror("Download Error", str(err)))
                self.after(0, self._close_panel)
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Download Error", str(err)))
            self.after(0, self._close_panel)

    def on_finish(self):
        messagebox.showinfo("Download Completed!", "Video files have been successfully downloaded.")
        self._close_panel()

    def append_log(self, text):
        if not self.winfo_exists():
            return
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def stop_download(self):
        self.cancel_requested = True
        self.queue_log("[download] Cancel requested...\n")
        self._close_panel()

    def _close_panel(self):
        if self._closed:
            return
        self._closed = True
        if self.on_finish_callback:
            self.on_finish_callback(self)
        if self.winfo_exists():
            self.destroy()

    def update_progress(self, percentage, speed):
        if not self.winfo_exists():
            return
        self.download_progress['value'] = percentage
        self.speed_display.config(text=f'Download Speed: {speed}')

    def queue_log(self, text):
        if self.winfo_exists():
            self.after(0, lambda t=text: self.append_log(t))

    def on_progress_update(self, data):
        if self.cancel_requested:
            raise DownloadCancelled()

        status = data.get("status")
        file_name = os.path.basename(data.get("filename") or "")
        if file_name:
            self.after(0, lambda n=file_name: self.downloading_name.config(text=n))

        if status == "downloading":
            percentage = self._percent_to_float(data.get("_percent_str"))
            speed = data.get("_speed_str", "N/A")
            self.after(0, lambda p=percentage, s=speed: self.update_progress(p, s))
        elif status == "finished":
            final_file = data.get("filename")
            if final_file and final_file not in self.downloaded_files:
                self.downloaded_files.append(final_file)

    def _percent_to_float(self, percent_str):
        if not percent_str:
            return 0.0
        cleaned = percent_str.replace("%", "").strip()
        try:
            return float(cleaned)
        except Exception:
            return 0.0

    def normalize_downloaded_audio(self):
        """
        Fallback: ensure every downloaded file ends with 44.1 kHz audio.
        We first prefer native 44.1 kHz streams in yt-dlp format selection;
        this post-step only re-encodes when the output is not already 44100 Hz.
        """
        unique_paths = []
        for path in self.downloaded_files:
            if path not in unique_paths:
                unique_paths.append(path)

        for media_path in unique_paths:
            if not os.path.exists(media_path):
                continue

            sample_rate = self.get_audio_sample_rate(media_path)
            if sample_rate == 44100:
                continue

            base, ext = os.path.splitext(media_path)
            temp_path = f"{base}_srfix{ext}"
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i", media_path,
                "-map", "0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-ar", "44100",
                temp_path
            ]

            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NO_WINDOW

            try:
                self.queue_log(f"[post] Resampling audio to 44.1kHz: {os.path.basename(media_path)}\n")
                result = subprocess.run(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=creation_flags
                )
                self.queue_log(result.stdout)

                if result.returncode == 0 and os.path.exists(temp_path):
                    os.replace(temp_path, media_path)
                elif os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.queue_log(f"[post] Failed to normalize sample rate: {e}\n")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    def get_audio_sample_rate(self, media_path):
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            media_path
        ]

        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            result = subprocess.run(
                probe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )
            if result.returncode != 0:
                return None
            value = result.stdout.strip()
            return int(value) if value.isdigit() else None
        except Exception:
            return None

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
        import re
        
        script_dir = pathlib.Path(Page.project_location) / "Script"
        script_dir.mkdir(parents=True, exist_ok=True)
        
        # Temp vtt file
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
        if re.match(video_regex, url) is None:
            messagebox.showerror('Invalid Link', "Please enter a valid video/playlist URL")
            return

        if url in self.active_downloads.values():
            messagebox.showwarning('Duplicate Download', "This URL is already being downloaded!")
            return

        if len(self.active_downloads) >= 2:
            messagebox.showwarning('Limit Reached', "You can only run a maximum of 2 downloads at a time.")
            return

        quality_key = app_config.get("clips_quality")
        format_commands = app_config.get("format_commands")
        command_prefix = format_commands["Clips"].get(quality_key)
        
        if not command_prefix:
            # Fallback if command is missing for some reason
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

        panel = DownloadingPanel(self.panels_frame, url, ydl_opts, on_finish_callback=self.on_download_complete)
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
        if re.match(video_regex, url) is None:
            messagebox.showerror('Invalid Link', "Please enter a valid video/playlist URL")
            return

        if url in self.active_downloads.values():
            messagebox.showwarning('Duplicate Download', "This URL is already being downloaded!")
            return

        if len(self.active_downloads) >= 2:
            messagebox.showwarning('Limit Reached', "You can only run a maximum of 2 downloads at a time.")
            return

        quality_key = app_config.get("proxy_quality")
        format_commands = app_config.get("format_commands")
        command_prefix = format_commands["Proxies"].get(quality_key)

        if not command_prefix:
            messagebox.showerror("Error", "Selected format command not found. Please reset settings.")
            return

        format_selector = extract_format_selector(command_prefix)
        if not format_selector:
            messagebox.showerror("Command Error", "Failed to parse selected format command.")
            return

        output_path = str(pathlib.Path(Page.project_location) / "Proxies" / "%(title)s_Proxy.%(ext)s")
        ydl_opts = {
            "format": format_selector,
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": False
        }
        apply_cookie_option(ydl_opts)

        panel = DownloadingPanel(self.panels_frame, url, ydl_opts, on_finish_callback=self.on_download_complete)
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

        # Proxy Quality & Codec
        proxy_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        proxy_frame.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(proxy_frame, text="Proxy Quality: ", font=("Poppins", 12), fg='white', bg="#1A1A1D").pack(side=tk.LEFT, padx=(0, 20))
        self.proxy_var = tk.StringVar(value=app_config.get("proxy_quality"))
        # Get labels from stored commands
        proxy_opts = list(app_config.get("format_commands")["Proxies"].keys())
        self.proxy_cb = ttk.Combobox(proxy_frame, textvariable=self.proxy_var, values=proxy_opts, state="readonly", font=("Poppins", 11), width=20)
        self.proxy_cb.pack(side=tk.LEFT)

        tk.Label(proxy_frame, text="Codec: ", font=("Poppins", 12), fg='white', bg="#1A1A1D").pack(side=tk.LEFT, padx=(30, 10))
        self.proxy_codec_var = tk.StringVar(value=app_config.get("proxy_codec"))
        codec_opts = list(CODEC_OPTIONS.keys())
        self.proxy_codec_cb = ttk.Combobox(proxy_frame, textvariable=self.proxy_codec_var, values=codec_opts, state="readonly", font=("Poppins", 11), width=20)
        self.proxy_codec_cb.pack(side=tk.LEFT)

        # Clips Quality & Codec
        clips_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        clips_frame.pack(fill=tk.X, padx=30, pady=10)

        tk.Label(clips_frame, text="Clips Quality: ", font=("Poppins", 12), fg='white', bg="#1A1A1D").pack(side=tk.LEFT, padx=(0, 20))
        self.clips_var = tk.StringVar(value=app_config.get("clips_quality"))
        clips_opts = list(app_config.get("format_commands")["Clips"].keys())
        self.clips_cb = ttk.Combobox(clips_frame, textvariable=self.clips_var, values=clips_opts, state="readonly", font=("Poppins", 11), width=20)
        self.clips_cb.pack(side=tk.LEFT)

        tk.Label(clips_frame, text="Codec: ", font=("Poppins", 12), fg='white', bg="#1A1A1D").pack(side=tk.LEFT, padx=(30, 10))
        self.clips_codec_var = tk.StringVar(value=app_config.get("clips_codec"))
        self.clips_codec_cb = ttk.Combobox(clips_frame, textvariable=self.clips_codec_var, values=codec_opts, state="readonly", font=("Poppins", 11), width=20)
        self.clips_codec_cb.pack(side=tk.LEFT)

        # Cookies Authentication
        cookies_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        cookies_frame.pack(fill=tk.X, padx=30, pady=10)

        self.use_cookies_var = tk.BooleanVar(value=bool(app_config.get("use_cookies")))
        self.use_cookies_cb = tk.Checkbutton(
            cookies_frame,
            text="Use Cookies for yt-dlp",
            variable=self.use_cookies_var,
            onvalue=True,
            offvalue=False,
            command=self.on_cookies_toggle,
            fg="white",
            bg="#1A1A1D",
            activebackground="#1A1A1D",
            activeforeground="white",
            selectcolor="#2B2B2B",
            font=("Poppins", 11)
        )
        self.use_cookies_cb.pack(side=tk.LEFT, padx=(0, 20))

        self.cookie_file_var = tk.StringVar(value=str(app_config.get("cookie_file") or ""))
        self.cookie_entry = tk.Entry(
            cookies_frame,
            textvariable=self.cookie_file_var,
            bg='#2B2B2B',
            fg='white',
            disabledbackground='#2D2D30',
            disabledforeground='#888888',
            insertbackground='white',
            relief='flat',
            font=('Poppins', 11),
            highlightthickness=1,
            highlightbackground='#3E3E42',
            highlightcolor='#DC143C'
        )
        self.cookie_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=6)
        self.cookie_entry.configure(state='disabled')

        self.cookie_select_button = tk.Button(
            cookies_frame,
            text='Select Cookie File',
            command=self.select_cookie_file,
            font=("Poppins", 10, "bold"),
            fg="white",
            bg='#DC143C',
            activebackground='#A60F2D',
            activeforeground='white',
            cursor="hand2",
            bd=0,
            relief="flat"
        )
        self.cookie_select_button.pack(side=tk.LEFT, ipady=6, ipadx=12)
        change_on_hover(self.cookie_select_button, '#FF1E4D', "#DC143C")
        self.on_cookies_toggle()

        # EJS Challenge Solver
        ejs_frame = tk.Frame(self.frame_content, bg='#1A1A1D')
        ejs_frame.pack(fill=tk.X, padx=30, pady=10)

        self.use_ejs_var = tk.BooleanVar(value=bool(app_config.get("use_ejs")))
        self.use_ejs_cb = tk.Checkbutton(
            ejs_frame,
            text="Solve JS Challenges (EJS)",
            variable=self.use_ejs_var,
            onvalue=True,
            offvalue=False,
            command=self.on_ejs_toggle,
            fg="white",
            bg="#1A1A1D",
            activebackground="#1A1A1D",
            activeforeground="white",
            selectcolor="#2B2B2B",
            font=("Poppins", 11)
        )
        self.use_ejs_cb.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(ejs_frame, text="JS Runtime: ", font=("Poppins", 11), fg='white', bg="#1A1A1D").pack(side=tk.LEFT)
        self.available_runtimes = get_available_js_runtimes()
        self.js_runtime_var = tk.StringVar(value=app_config.get("js_runtime") or "node")
        
        # If saved runtime is not available, pick the first available one
        if self.js_runtime_var.get() not in self.available_runtimes and self.available_runtimes:
            self.js_runtime_var.set(self.available_runtimes[0])

        self.js_runtime_cb = ttk.Combobox(ejs_frame, textvariable=self.js_runtime_var, values=self.available_runtimes if self.available_runtimes else ["None Found"], state="readonly", font=("Poppins", 11), width=10)
        self.js_runtime_cb.pack(side=tk.LEFT)
        
        # Initial validation
        self.on_ejs_toggle(initial=True)

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

    def on_cookies_toggle(self):
        is_enabled = self.use_cookies_var.get()
        if is_enabled:
            self.cookie_entry.configure(state='normal')
            self.cookie_select_button.configure(state='normal', bg='#DC143C')
        else:
            self.cookie_entry.configure(state='disabled')
            self.cookie_select_button.configure(state='disabled', bg='#3E3E42')

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
        old_proxy_codec = app_config.get("proxy_codec")
        old_clips_codec = app_config.get("clips_codec")
        
        new_proxy_codec = self.proxy_codec_var.get()
        new_clips_codec = self.clips_codec_var.get()
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

        app_config.set("proxy_quality", self.proxy_var.get())
        app_config.set("clips_quality", self.clips_var.get())
        app_config.set("proxy_codec", new_proxy_codec)
        app_config.set("clips_codec", new_clips_codec)
        app_config.set("use_cookies", use_cookies)
        app_config.set("cookie_file", cookie_file)
        app_config.set("use_ejs", use_ejs)
        app_config.set("js_runtime", js_runtime)
        
        # If codec changed, regenerate relevant commands
        if old_proxy_codec != new_proxy_codec:
            app_config.regenerate_commands("Proxies")
        if old_clips_codec != new_clips_codec:
            app_config.regenerate_commands("Clips")
            
        messagebox.showinfo("Success", "Settings have been safely updated.")

    def reset_settings(self):
        self.proxy_var.set("360p")
        self.clips_var.set("Best Available")
        self.proxy_codec_var.set("H.264 (Compatible)")
        self.clips_codec_var.set("H.264 (Compatible)")
        self.use_cookies_var.set(False)
        self.cookie_file_var.set("")
        self.on_cookies_toggle()
        
        app_config.set("proxy_quality", "360p")
        app_config.set("clips_quality", "Best Available")
        app_config.set("proxy_codec", "H.264 (Compatible)")
        app_config.set("clips_codec", "H.264 (Compatible)")
        app_config.set("use_cookies", False)
        app_config.set("cookie_file", "")
        app_config.set("use_ejs", True)
        app_config.set("js_runtime", "node")
        
        app_config.regenerate_all_commands()
        
        messagebox.showinfo("Reset", "Settings have been reverted to defaults.")
