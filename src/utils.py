
import shutil

def check_dependencies():
    """Check if required external tools are available in PATH"""
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("FFmpeg")
    if not shutil.which("yt-dlp"):
        missing.append("yt-dlp")
    return missing

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