# PreCut - Content Workflow Helper 🎬

A modern, dark-themed desktop application designed to streamline YouTube content creation workflows. **PreCut** provides a centralized interface for generating transcripts, downloading high-quality clips, and managing low-resolution proxies with real-time feedback and smart concurrency management.

---

## ✨ Features

- **📺 Transcript Generator**: Automatically fetch and clean YouTube transcripts. Strips WebVTT formatting, timestamps, and redundant tags to give you a clean, usable script instantly.
- **📥 Clips Downloader**: Download high-quality video clips directly into your project folders. Features a custom inline terminal log for real-time `yt-dlp` transparency.
- **⚡ Proxy Downloader**: Create lightweight proxies (360p/480p) for faster editing timelines.
- **⚙️ Persistent Settings**: Configure global download quality and project paths once. Settings are stored securely in your user Documents folder, persisting between sessions.
- **🏗️ Smart Concurrency**: Built-in protection allows up to 2 concurrent downloads per page with duplicate URL detection to prevent resource waste.
- **🧹 Clean Workspace**: Automated `__pycache__` relocation and temporary file cleanup to keep your project source code pristine.

---

## 🛠️ Tech Stack

- **UI Framework**: Modernized Python `Tkinter` (Custom Dark Theme)
- **Image Processing**: `Pillow`
- **Backend Engine**: `yt-dlp`
- **Storage**: Persistent JSON-based configuration

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **yt-dlp**: Ensure `yt-dlp` is installed and accessible in your system's PATH.
- **FFmpeg**: Required for `yt-dlp` to merge high-quality video/audio streams.

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/PreCut.git
   cd PreCut
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python src/main.py
   ```

---

## 📂 Project Structure

```text
PreCut/
├── assets/             # UI Icons and Brand Assets
├── src/
│   ├── main.py        # Entry point and sidebar navigation
│   ├── page_view.py   # Core UI Components and Logic
│   ├── config.py      # AppConfig and Path Management
│   └── utils.py       # Theme Helpers and Hover Effects
├── requirements.txt    # External dependencies
└── README.md
```

---

## 📝 Configuration

PreCut stores its data outside the source folder to ensure a portable and clean development environment:
- **Settings Path**: `~/Documents/PreCut/data/settings.json`
- **Cache Path**: `~/Documents/PreCut/data/pycache/`

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for any UI improvements or backend feature additions.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
