import yt_dlp
import ffmpeg
import os
from typing import Callable, List, Optional
from .models import DownloadOption, StreamInfo, DownloadState


class Downloader:
    def __init__(self):
        self.output_dir = "downloads"
        os.makedirs(self.output_dir, exist_ok=True)

    def get_video_info(self, url: str) -> List[dict]:
        ydl_opts = {
            "quiet": True,
            "extract_flat": "in_playlist",  # Extract playlist entries without full details
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        videos = []
        # Handle single video or playlist
        entries = info.get("entries", [info]) if "entries" in info else [info]

        for entry in entries:
            video_id = entry.get("id", "unknown")
            title = entry.get("title", "Unknown Title")
            thumbnail = entry.get("thumbnail", "")

            # Fetch detailed stream info for each video
            stream_info = self._fetch_stream_info(entry.get("url", url))
            streams = self._parse_streams(stream_info)
            options = self._create_download_options(video_id, title, thumbnail, streams)

            videos.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "thumbnail": thumbnail,
                    "options": options,
                }
            )

        return videos

    def _fetch_stream_info(self, url: str) -> dict:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(url, download=False)

    def _parse_streams(self, info: dict) -> List[StreamInfo]:
        streams = []
        for fmt in info.get("formats", []):
            format_id = fmt.get("format_id")
            ext = fmt.get("ext")
            url = fmt.get("url")

            if not (format_id and ext and url):
                continue

            is_audio = fmt.get("vcodec") == "none"
            resolution = fmt.get("resolution") if not is_audio else None
            bitrate = fmt.get("abr") if is_audio else None
            file_size = fmt.get("filesize") or fmt.get("filesize_approx")

            streams.append(
                StreamInfo(
                    url=url,
                    format_id=format_id,
                    ext=ext,
                    resolution=resolution,
                    bitrate=str(bitrate) if bitrate else None,
                    is_audio=is_audio,
                    file_size=file_size,
                )
            )
        return streams

    def _create_download_options(
        self, video_id: str, title: str, thumbnail: str, streams: List[StreamInfo]
    ) -> List[DownloadOption]:
        options = []

        # Video + Audio (combined streams)
        for stream in streams:
            if not stream.is_audio and stream.ext in ["mp4", "webm"]:
                label = f"Video+Audio: {stream.resolution or 'Unknown'} ({stream.ext})"
                requires_conversion = stream.ext != "mp4"
                options.append(
                    DownloadOption(
                        label=label,
                        video_id=video_id,
                        title=title,
                        thumbnail=thumbnail,
                        file_size=stream.file_size,
                        requires_conversion=requires_conversion,
                        video_stream=stream,
                        output_format="mp4",
                    )
                )

        # Video + Audio (separate streams)
        video_streams = [s for s in streams if not s.is_audio]
        audio_streams = [s for s in streams if s.is_audio]
        for video in video_streams:
            for audio in audio_streams:
                label = f"Video: {video.resolution or 'Unknown'} + Audio: {audio.bitrate or 'Unknown'}kbps"
                total_size = (video.file_size or 0) + (audio.file_size or 0)
                options.append(
                    DownloadOption(
                        label=label,
                        video_id=video_id,
                        title=title,
                        thumbnail=thumbnail,
                        file_size=total_size if total_size > 0 else None,
                        requires_merging=True,
                        video_stream=video,
                        audio_stream=audio,
                        output_format="mp4",
                    )
                )

        # Audio Only
        for stream in audio_streams:
            label = f"Audio: {stream.bitrate or 'Unknown'}kbps ({stream.ext})"
            requires_conversion = stream.ext != "mp3"
            options.append(
                DownloadOption(
                    label=label,
                    video_id=video_id,
                    title=title,
                    thumbnail=thumbnail,
                    file_size=stream.file_size,
                    requires_conversion=requires_conversion,
                    audio_stream=stream,
                    output_format="mp3",
                )
            )

        return options

    def download(
        self,
        option: DownloadOption,
        progress_callback: Callable[[DownloadState, float], None],
    ):
        progress_callback(DownloadState.PENDING, 0)

        output_file = os.path.join(
            self.output_dir,
            f"{option.title[:50]}_{option.label.replace(':', '_').replace(' ', '_')}.{option.output_format}",
        )

        if option.video_stream and option.audio_stream:
            # Download separate video and audio, then merge
            video_path = self._download_stream(
                option.video_stream, "temp_video", progress_callback
            )
            audio_path = self._download_stream(
                option.audio_stream, "temp_audio", progress_callback
            )
            self._merge_streams(video_path, audio_path, output_file, progress_callback)
        elif option.video_stream:
            # Download video directly
            self._download_stream(option.video_stream, output_file, progress_callback)
            if option.video_stream.ext != "mp4":
                self._convert_to_mp4(
                    output_file, output_file + ".mp4", progress_callback
                )
                os.rename(output_file + ".mp4", output_file)
        elif option.audio_stream:
            # Download audio directly
            self._download_stream(option.audio_stream, output_file, progress_callback)
            if option.output_format == "mp3" and option.audio_stream.ext != "mp3":
                self._convert_to_mp3(
                    output_file, output_file + ".mp3", progress_callback
                )
                os.rename(output_file + ".mp3", output_file)

        progress_callback(DownloadState.FINISHED, 1)

    def _download_stream(
        self,
        stream: StreamInfo,
        output: str,
        progress_callback: Callable[[DownloadState, float], None],
    ) -> str:
        progress_callback(DownloadState.DOWNLOADING, 0)
        output_path = os.path.join(self.output_dir, f"{output}.{stream.ext}")

        def progress_hook(d):
            if d["status"] == "downloading":
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
                progress = d.get("downloaded_bytes", 0) / total_bytes
                progress_callback(
                    DownloadState.DOWNLOADING, min(progress * 0.8, 0.8)
                )  # Reserve 20% for post-processing

        ydl_opts = {
            "format": stream.format_id,
            "outtmpl": output_path,
            "quiet": True,
            "progress_hooks": [progress_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([stream.url])

        return output_path

    def _merge_streams(
        self,
        video_path: str,
        audio_path: str,
        output: str,
        progress_callback: Callable[[DownloadState, float], None],
    ):
        progress_callback(DownloadState.MERGING, 0.85)
        try:
            video_stream = ffmpeg.input(video_path)
            audio_stream = ffmpeg.input(audio_path)
            ffmpeg.output(
                video_stream,
                audio_stream,
                output,
                vcodec="copy",
                acodec="aac",
                strict="experimental",
                loglevel="quiet",
            ).run(overwrite_output=True)
            os.remove(video_path)
            os.remove(audio_path)
        except ffmpeg.Error:
            raise Exception("Failed to merge streams")

    def _convert_to_mp4(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Callable[[DownloadState, float], None],
    ):
        progress_callback(DownloadState.CONVERTING, 0.9)
        try:
            ffmpeg.input(input_path).output(
                output_path,
                vcodec="copy",
                acodec="aac",
                strict="experimental",
                loglevel="quiet",
            ).run(overwrite_output=True)
            os.remove(input_path)
        except ffmpeg.Error:
            raise Exception("Failed to convert to MP4")

    def _convert_to_mp3(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Callable[[DownloadState, float], None],
    ):
        progress_callback(DownloadState.CONVERTING, 0.9)
        try:
            ffmpeg.input(input_path).output(
                output_path, acodec="mp3", loglevel="quiet"
            ).run(overwrite_output=True)
            os.remove(input_path)
        except ffmpeg.Error:
            raise Exception("Failed to convert to MP3")
