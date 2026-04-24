import os
import sys
import shutil

def get_asset_path(relative_path):
    """ Get absolute path to asset, works for dev and for Nuitka onefile """
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # During dev: utils.py is in src/, assets are in ../assets
    # During Nuitka build: common to flatten src, making assets a sibling
    
    # Try sibling first (bundled mode)
    path = os.path.join(base_path, relative_path)
    if os.path.exists(path):
        return path
        
    # Try one level up (dev mode)
    return os.path.join(base_path, "..", relative_path)

def check_dependencies():
    """Check if required external tools are available in PATH"""
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("FFmpeg")
    return missing

def get_available_js_runtimes():
    """Detect available JS runtimes on the system"""
    runtimes = []
    if shutil.which("node"):
        runtimes.append("node")
    if shutil.which("deno"):
        runtimes.append("deno")
    if shutil.which("bun"):
        runtimes.append("bun")
    if shutil.which("qjs"):
        runtimes.append("quickjs")
    return runtimes

# function to change properties of button on hover
def change_on_hover(button, colorOnHover, colorOnLeave):

    # adjusting background of the widget
    # background on entering widget
    button.bind("<Enter>", func=lambda e: button.config(
        background=colorOnHover))

    # background color on leving widget
    button.bind("<Leave>", func=lambda e: button.config(
        background=colorOnLeave))
    
video_regex = (
    r'(https?://)?(www\.|m\.)?'
    r'(youtube\.com|youtu\.be)'
    r'(/(?:[\w\-]+\?v=|embed/|v/|shorts/)?)([\w\-]+)(\S+)?'
)