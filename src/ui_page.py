import os
import shlex
import shutil

import customtkinter as ctk

from config import app_config


class Page(ctk.CTkFrame):
    project_location = ""
    def __init__(self, master, **kw):
        if 'fg_color' not in kw:
            kw['fg_color'] = '#1A1A1D'
        super().__init__(master, **kw)


def apply_cookie_option(ydl_opts):
    ydl_opts["no_color"] = True

    use_cookies = bool(app_config.get("use_cookies"))
    cookie_file = str(app_config.get("cookie_file") or "").strip()
    if use_cookies and cookie_file:
        ydl_opts["cookiefile"] = os.path.normpath(cookie_file).replace("\\", "/")

    if bool(app_config.get("use_ejs")):
        runtime = app_config.get("js_runtime")
        if runtime and shutil.which(runtime):
            ydl_opts["remote_components"] = ["ejs:github"]
            ydl_opts["js_runtimes"] = {runtime: {}}


def extract_format_selector(command_prefix):
    parts = shlex.split(command_prefix)
    for idx, part in enumerate(parts):
        if part in ("-f", "--format") and idx + 1 < len(parts):
            return parts[idx + 1]
    return None
