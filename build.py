"""
PreCut Build Script
Generates a single portable .exe using PyInstaller.

Usage:
    python build.py          # Clean build
    python build.py --fast   # Skip clean, just rebuild
"""

import subprocess
import sys
import os
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ENTRY_POINT = os.path.join("src", "main.py")
ICON_PATH = os.path.join("assets", "precut.ico")
ASSETS_DIR = os.path.join("assets", "*")

APP_NAME = "PreCut"
VERSION_FILE = "version_info.txt"


def clean():
    """Remove previous build artifacts."""
    for d in ("build", "dist"):
        path = os.path.join(PROJECT_ROOT, d)
        if os.path.isdir(path):
            print(f"  Cleaning {d}/ ...")
            shutil.rmtree(path)
    for f in ("PreCut.spec",):
        path = os.path.join(PROJECT_ROOT, f)
        if os.path.isfile(path):
            print(f"  Removing {f} ...")
            os.remove(path)


def build():
    """Run PyInstaller to produce a single .exe."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name={APP_NAME}",
        "--onefile",
        "--windowed",
        f"--version-file={VERSION_FILE}",
        f"--icon={ICON_PATH}",
        "--paths=src",
        f"--add-data={ASSETS_DIR};assets",
        "--collect-all=customtkinter",
        "--collect-data=yt_dlp",
        ENTRY_POINT,
    ]

    print(f"Building {APP_NAME}.exe ...")
    print(f"  Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print(f"\nBuild FAILED (exit code {result.returncode})")
        sys.exit(1)

    exe_path = os.path.join(PROJECT_ROOT, "dist", f"{APP_NAME}.exe")
    if os.path.isfile(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\nBuild successful!")
        print(f"  Output: {exe_path}")
        print(f"  Size:   {size_mb:.1f} MB")
    else:
        print(f"\nBuild completed but {APP_NAME}.exe not found in dist/")
        sys.exit(1)


if __name__ == "__main__":
    skip_clean = "--fast" in sys.argv

    if not skip_clean:
        clean()
    build()
