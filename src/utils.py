
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