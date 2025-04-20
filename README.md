# Vertex

Vertex is a sleek, powerful, and intuitive Python-based GUI application for downloading videos and audio from URLs. It leverages the `vertex-downloader` library for downloading and processing, wrapped in a professional neobrutalist design with a light color palette.

```python
import customtkinter
from vertex_downloader.downloader import Downloader
```

## Features

- Paste a URL to fetch video and audio stream information for single videos or playlists.
- View download options in two tabs: Video+Sound and Audio Only, with:
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

4. Install the `vertex-downloader` library (if not using a local path):

   ```powershell
   pip install vertex-downloader
   ```

   Or, if using a local copy:

   ```powershell
   pip install -e ../vertex_downloader
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

3. Paste a video or playlist URL, select a download option from the Video+Sound or Audio Only tab, and start the download.

## Project Structure

```text
Vertex/
├── assets/                   # Logo and static assets
├── src/                      # Source code
│   ├── gui/                  # GUI components
│   └── main.py               # Application entry point
├── README.md                 # Documentation
├── requirements.txt          # Dependencies
└── setup.ps1                 # Setup script
```

## License

MIT License
