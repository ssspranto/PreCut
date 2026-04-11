# Contributing to PreCut 🚀

First off, thank you for considering contributing to **PreCut**! It’s people like you that make the open-source community such an amazing place to learn, inspire, and create.

---

## 🛣️ 2026 - 2027 Roadmap

We have big plans for PreCut! Here are the core areas where we need your help:

### 🎨 UI & UX Improvements
- [ ] **Custom Title Bar**: Replace the default Windows title bar with a matching dark-themed custom implementation.
- [ ] **Drag & Drop**: Allow users to drag a URL from their browser directly into the app.
- [ ] **Dynamic Animations**: Add subtle transitions when switching between pages.
- [ ] **System Tray Integration**: Minimize the app to the tray while long downloads are running.

### 🛠️ Feature Expansion
- [ ] **Internal Trimmer**: Add a "Trim & Cut" tab where users can use FFmpeg to cut specific segments without re-encoding.
- [ ] **Batch Processing**: A dedicated queue manager for handling lists of dozens of URLs.
- [ ] **Multi-Language Support**: Expand the Transcript Generator to support automatic detection and cleaning for non-English subtitles.
- [ ] **Audio-Only Mode**: A simple toggle to extract high-quality MP3/WAV files for podcasts.

### ⚙️ Backend & Performance
- [x] **Portable Build script**: Create a robust `build.py` or use Nuitka to generate a one-click `.exe`.
- [ ] **Error Handling**: Implement more granular error parsing for complex `yt-dlp` output failures.
- [ ] **Plugin System**: Allow users to add their own custom `yt-dlp` command strings via the Settings page.

---

## 🛠️ How to Contribute

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/yourusername/PreCut.git
   ```
3. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/amazing-new-feature
   ```
4. **Commit** your changes with descriptive messages:
   ```bash
   git commit -m 'Add some amazing feature'
   ```
5. **Push** to the branch:
   ```bash
   git push origin feature/amazing-new-feature
   ```
6. **Open a Pull Request** and describe what you've changed!

---

## 💬 Communication
For major changes, please open an issue first to discuss what you would like to change. This ensures your hard work aligns with the project's direction!

---

## ⚖️ Code of Conduct
Please be respectful and helpful. We follow the standard [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md) for this project.
