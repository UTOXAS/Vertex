# Vertex

Vertex is a sleek, powerful, and intuitive Python-based GUI application for downloading videos and audio from URLs. It leverages yt-dlp for downloading and ffmpeg for processing, wrapped in a professional neobrutalist design with a light color palette.

```python
import customtkinter
import yt_dlp
import ffmpeg
```

## Features

- Paste a URL to fetch video and audio stream information for single videos or playlists.
- View a list of download options, each displaying:
  - Video thumbnail
  - Video title
  - Quality (resolution or bitrate)
  - Estimated file size
  - Processing requirements (CONVERTING, MERGING, or none)
- Download with progress tracking (PENDING, DOWNLOADING, CONVERTING, MERGING, FINISHED).
- Modern neobrutalist UI with light colors.

## Prerequisites

- Python 3.11
- FFmpeg installed and added to system PATH (required for media processing)
- The ffmpeg-python library (automatically installed via requirements.txt)
- Windows 10 with PowerShell

## Installation

1. Clone the repository:

   ```powershell
   git clone <repository-url>
   cd Vertex
   ```

2. Run the setup script to create a virtual environment and install dependencies:

   ```powershell
   .\setup.ps1
   ```

3. Ensure FFmpeg is installed:

   ```powershell
   choco install ffmpeg
   ```

## Usage

1. Activate the virtual environment:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. Run the application:

   ```powershell
   py -3.11 .\src\main.py
   ```

3. Paste a video or playlist URL, select a download option, and start the download.

## Project Structure

```text
Vertex/
├── assets/                   # Logo and static assets
├── src/                      # Source code
│   ├── gui/                  # GUI components
│   ├── backend/              # Backend logic
│   └── main.py               # Application entry point
├── README.md                 # Documentation
├── requirements.txt          # Dependencies
└── setup.ps1                 # Setup script
```

## License

MIT License
