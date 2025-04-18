# Vertex

Vertex is a sleek, powerful, and intuitive Python-based GUI application for downloading videos and audio from URLs. It leverages yt-dlp for downloading and ffmpeg for processing, wrapped in a professional neobrutalist design with a light color palette.

```python
import customtkinter
import yt_dlp
import ffmpeg
```

Features
Paste a URL to fetch video and audio stream information.
View video thumbnails, titles, and available download options (video+audio, audio-only).
Download with progress tracking (PENDING, DOWNLOADING, CONVERTING, MERGING, FINISHED).
Modern neobrutalist UI with light colors.
Prerequisites
Python 3.11
ffmpeg installed and added to system PATH
Windows 10 with PowerShell
Installation
Clone the repository: ```powershell git clone <repository-url> cd Vertex```
Run the setup script to create a virtual environment and install dependencies: ```powershell .\setup.ps1```
Ensure ffmpeg is installed: ```powershell choco install ffmpeg```
Usage
Activate the virtual environment: ```powershell .\venv\Scripts\Activate.ps1```
Run the application: ```powershell py -3.11 .\src\main.py```
Paste a video URL, select a download option, and start the download.
Project Structure

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

License
MIT License
