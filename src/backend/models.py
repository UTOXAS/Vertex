from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class DownloadState(Enum):
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    CONVERTING = "Converting"
    MERGING = "Merging"
    FINISHED = "Finished"
    CANCELED = "Canceled"
    FAILED = "Failed"


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
    video_id: str
    title: str
    thumbnail: str
    file_size: Optional[int] = None  # In bytes
    requires_conversion: bool = False
    requires_merging: bool = False
    video_stream: Optional[StreamInfo] = None
    audio_stream: Optional[StreamInfo] = None
    output_format: str = "mp4"  # mp4 or mp3

    @property
    def quality_key(self) -> tuple:
        """Return a sorting key based on quality (resolution or bitrate)."""
        if self.audio_stream and not self.video_stream:
            # Audio-only: sort by bitrate (higher is better)
            try:
                bitrate = int(self.audio_stream.bitrate or "0")
                return (2, bitrate, self.label)
            except (ValueError, TypeError):
                return (2, 0, self.label)
        else:
            # Video+Sound: sort by resolution (higher is better)
            resolution = self.video_stream.resolution if self.video_stream else "0p"
            try:
                # Extract number from resolution (e.g., "1080p" -> 1080)
                res_num = int(resolution.lower().replace("p", ""))
                return (1, res_num, self.label)
            except (ValueError, TypeError):
                return (1, 0, self.label)
