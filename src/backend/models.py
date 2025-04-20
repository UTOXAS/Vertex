from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class DownloadState(Enum):
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    CONVERTING = "Converting"
    MERGING = "Merging"
    FINISHED = "Finished"


@dataclass
class StreamInfo:
    url: str
    format_id: str
    ext: str
    resolution: Optional[str] = None
    bitrate: Optional[str] = None
    is_audio: bool = False
    file_size: Optional[int] = None  # In bytes


@dataclass
class DownloadOption:
    label: str
    video_id: str  # Unique identifier for the video
    title: str
    thumbnail: str
    file_size: Optional[int] = None  # In bytes
    requires_conversion: bool = False
    requires_merging: bool = False
    video_stream: Optional[StreamInfo] = None
    audio_stream: Optional[StreamInfo] = None
    output_format: str = "mp4"  # mp4 or mp3
