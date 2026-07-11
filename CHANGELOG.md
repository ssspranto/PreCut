# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-04-26

### Added
- **Pause & Resume Downloads**: Implemented a stop-and-resume mechanism for both Clips and Proxies. Downloads can now be paused mid-flight and resumed later, picking up from the existing partial file.
- **Improved Thumbnail Support**: Added a persistent reference system for thumbnails to prevent garbage collection issues and a User-Agent header to ensure reliable fetching.

### Changed
- **Default EJS Runtime**: Switched the default JavaScript runtime from `node` to `deno` for better out-of-the-box performance with yt-dlp challenges.
- **Optimized Packaging**: Updated the build process to fully support Nuitka standalone distribution for `customtkinter` and `yt_dlp`.

### Fixed
- **Thumbnail Crashes**: Resolved a `NameError` and potential `TclError` when updating thumbnails on panels that were closed while a background fetch was active.
- **Dependency Audit**: Updated `requirements.txt` with missing core packages (`customtkinter`, `requests`).

## [1.1.4] - 2026-04-24

### Added
- **EJS (External JavaScript) Support**: Implemented support for yt-dlp's EJS challenge solver to bypass complex YouTube JS/Botguard challenges without a full browser.
- **Smart Runtime Detection**: Added an automatic system check that detects installed JS runtimes (Node.js, Deno, Bun, or QuickJS) and prevents enabling EJS if no runtime is found.
- **JS Runtime Selector**: Added a new Settings section to configure the preferred JavaScript runtime for EJS execution, filtered by installed options.
- **Remote Script Updates**: Enabled automatic fetching of the latest challenge solver scripts directly from GitHub.

### Fixed
- **Clean UI Progress**: Resolved an issue where ANSI color codes (e.g., `[0;32m`) were visible in the download speed and progress labels.
- **Improved Path Handling**: Added normalization for cookie file paths to prevent issues with Windows backslashes in yt-dlp.

## [1.1.3] - 2026-04-21

### Changed
- **yt_dlp Package Migration**: Fully migrated the backend from using the `yt-dlp` command-line executable to the native `yt_dlp` Python package.
- Removed the requirement to have the `yt-dlp` executable installed in the system's PATH. It is now installed automatically as a Python library via `pip install -r requirements.txt`.
- Advanced settings now pass `yt_dlp` arguments as native Python dictionaries instead of raw command strings.

## [1.1.2] - 2026-04-20

### Added
- Added a new **toggleable cookies option** in Settings for yt-dlp integrations, disabled by default.
- Added persistent cookie settings in `settings.json` via `use_cookies` and `cookie_file`.

### Changed
- Unified audio sample-rate handling for both Clips and Proxy downloads to target **44.1 kHz** by default.
- Download format selection now **prefers native 44.1 kHz audio streams** first (`asr=44100`) and keeps broader fallbacks to avoid failed downloads on limited sources.
- Refactored Transcript, Clips, and Proxy flows to use the **`yt_dlp` Python API** instead of subprocess shell commands, preserving live log/progress updates while improving cancellation and error handling.
- When cookies are enabled, all yt-dlp operations (Transcript Generator, Clips Downloader, Proxy Downloader) now use the selected `cookiefile` setting.

### Fixed
- Resolved inconsistent output sample rates where Proxy downloads could end up at **48 kHz** while Clips were **44.1 kHz**.
- Added a post-download fallback that inspects outputs with `ffprobe` and, only when needed, normalizes audio to **44100 Hz** via `ffmpeg` while preserving video streams (`-c:v copy`).

## [1.1.1] - 2026-04-19

### Fixed
- Proxy Downloader output filenames now use the pattern **`basename_Proxy.ext`** (e.g. `MyVideo_Proxy.mp4`) instead of **`basename.ext_proxy`**, so the file keeps a valid video extension for editors and the OS.

## [1.1.0] - 2026-04-12

### Added
- **Codec Selector**: New dropdowns in Settings for selecting preferred video codecs (H.264, AV1, VP9) for both Clips and Proxies.
- **Power User Commands**: The application now stores the entire `yt-dlp` command string in `settings.json`, allowing for advanced customization of download parameters.
- **Improved Compatibility**: Default settings now prioritize the H.264 (avc1) codec to ensure out-of-the-box compatibility with video editors like Adobe Premiere Pro.

### Fixed
- Resolved import errors in Premiere Pro caused by the `av01` (AV1) codec being downloaded by default on some videos.
- Fixed a bug where quality settings were not correctly mapped to full command strings in previous experimental builds.

## [1.0.0] - 2026-04-11

### Added
- **Transcript Generator**: Automated fetching and cleaning of YouTube transcripts (strips WebVTT and timestamps).
- **Clips Downloader**: High-quality video downloads with integrated terminal logs.
- **Proxy Downloader**: Lightweight proxy generation (360p/480p) for editing.
- **Standalone Build**: Support for Nuitka standalone `.exe` generation.
- **Persistent Configuration**: Settings stored in `~/Documents/PreCut/` to survive session restarts.
- **Modern UI**: Dark-themed custom Tkinter interface with responsive sidebar.

### Changed
- Refactored asset path resolution to support both development and bundled executable modes.
- Relocated `__pycache__` to user documents to keep the source directory clean.

### Fixed
- Resolved executable crashes caused by relative asset paths in bundled builds.
- Mitigation for Windows Defender false-positive flags by switching to standalone distribution.
