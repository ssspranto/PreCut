# Changelog

All notable changes to this project will be documented in this file.

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
