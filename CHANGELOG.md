# Changelog

All notable changes to this project will be documented in this file.

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
