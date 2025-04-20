import yt_dlp
import ffmpeg
import os
from typing import Callable, List, Optional
from .models import DownloadOption, StreamInfo, DownloadState


class Downloader:
    def __init__(self):
        self.output_dir = "downloads"
        os.makedirs(self.output_dir, exist_ok=True)
        self._cancel = False
        self._downloaded_bytes = 0

    def cancel(self):
        """Signal the downloader to cancel the current operation."""
        self._cancel = True

    def get_video_info(self, url: str) -> List[dict]:
        self._cancel = False
        ydl_opts = {
            "quiet": True,
            "extract_flat": "in_playlist",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        videos = []
        entries = info.get("entries", [info]) if "entries" in info else [info]

        # Cache stream info to avoid redundant calls
        stream_cache = {}
        for entry in entries:
            if self._cancel:
                return []

            video_id = entry.get("id", "unknown")
            title = entry.get("title", "Unknown Title")
            thumbnail = entry.get("thumbnail", "")

            video_url = entry.get("url", url)
            stream_info = stream_cache.get(video_url)
            if not stream_info:
                stream_info = self._fetch_stream_info(video_url)
                stream_cache[video_url] = stream_info

            streams = self._parse_streams(stream_info)
            options = self._create_download_options(video_id, title, thumbnail, streams)
            # Sort options by quality
            options.sort(key=lambda opt: opt.quality_key, reverse=True)

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

        # Combined Video+Audio Streams
        for stream in streams:
            if not stream.is_audio and stream.ext in ["mp4", "webm"]:
                label = f"Combined: {stream.resolution or 'Unknown'} ({stream.ext})"
                requires_conversion = stream.ext != "mp4"
                output_format = "mp4" if requires_conversion else stream.ext
                options.append(
                    DownloadOption(
                        label=label,
                        video_id=video_id,
                        title=title,
                        thumbnail=thumbnail,
                        file_size=stream.file_size,
                        requires_conversion=requires_conversion,
                        video_stream=stream,
                        output_format=output_format,
                        convert_to_standard=requires_conversion,
                    )
                )

        # Separate Video+Audio Streams (Requires Merging)
        video_streams = [s for s in streams if not s.is_audio]
        audio_streams = [s for s in streams if s.is_audio]
        for video in video_streams:
            for audio in audio_streams:
                label = f"Merge: Video {video.resolution or 'Unknown'} + Audio {audio.bitrate or 'Unknown'}kbps"
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
                        convert_to_standard=True,
                    )
                )

        # Audio-Only Streams
        for stream in audio_streams:
            label = f"Audio: {stream.bitrate or 'Unknown'}kbps ({stream.ext})"
            requires_conversion = stream.ext != "mp3"
            output_format = "mp3" if requires_conversion else stream.ext
            options.append(
                DownloadOption(
                    label=label,
                    video_id=video_id,
                    title=title,
                    thumbnail=thumbnail,
                    file_size=stream.file_size,
                    requires_conversion=requires_conversion,
                    audio_stream=stream,
                    output_format=output_format,
                    convert_to_standard=requires_conversion,
                )
            )

        return options

    def download(
        self,
        option: DownloadOption,
        progress_callback: Callable[[DownloadState, float, int, Optional[int]], None],
    ):
        self._cancel = False
        self._downloaded_bytes = 0
        progress_callback(DownloadState.PENDING, 0, 0, option.file_size)

        output_file = os.path.join(
            self.output_dir,
            f"{option.title[:50]}_{option.label.replace(':', '_').replace(' ', '_')}.{option.output_format}",
        )

        try:
            if self._cancel:
                progress_callback(DownloadState.CANCELED, 0, 0, option.file_size)
                return

            if option.video_stream and option.audio_stream:
                # Separate streams requiring merging
                video_path = self._download_stream(
                    option.video_stream, "temp_video", progress_callback
                )
                if self._cancel:
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    progress_callback(DownloadState.CANCELED, 0, 0, option.file_size)
                    return

                audio_path = self._download_stream(
                    option.audio_stream, "temp_audio", progress_callback
                )
                if self._cancel:
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    progress_callback(DownloadState.CANCELED, 0, 0, option.file_size)
                    return

                self._merge_streams(
                    video_path, audio_path, output_file, progress_callback
                )
            elif option.video_stream:
                # Combined video+audio stream
                self._download_stream(
                    option.video_stream, output_file, progress_callback
                )
                if self._cancel:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    progress_callback(DownloadState.CANCELED, 0, 0, option.file_size)
                    return

                if option.requires_conversion and option.convert_to_standard:
                    temp_output = output_file + ".mp4"
                    self._convert_to_mp4(output_file, temp_output, progress_callback)
                    if self._cancel:
                        if os.path.exists(output_file):
                            os.remove(output_file)
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                        progress_callback(
                            DownloadState.CANCELED, 0, 0, option.file_size
                        )
                        return
                    os.rename(temp_output, output_file)
            elif option.audio_stream:
                # Audio-only stream
                self._download_stream(
                    option.audio_stream, output_file, progress_callback
                )
                if self._cancel:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    progress_callback(DownloadState.CANCELED, 0, 0, option.file_size)
                    return

                if option.requires_conversion and option.convert_to_standard:
                    temp_output = output_file + ".mp3"
                    self._convert_to_mp3(output_file, temp_output, progress_callback)
                    if self._cancel:
                        if os.path.exists(output_file):
                            os.remove(output_file)
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                        progress_callback(
                            DownloadState.CANCELED, 0, 0, option.file_size
                        )
                        return
                    os.rename(temp_output, output_file)

            if not self._cancel:
                progress_callback(
                    DownloadState.FINISHED, 1, self._downloaded_bytes, option.file_size
                )
        except Exception as e:
            progress_callback(
                DownloadState.FAILED, 0, self._downloaded_bytes, option.file_size
            )
            if os.path.exists(output_file):
                os.remove(output_file)

    def _download_stream(
        self,
        stream: StreamInfo,
        output: str,
        progress_callback: Callable[[DownloadState, float, int, Optional[int]], None],
    ) -> str:
        progress_callback(
            DownloadState.DOWNLOADING, 0, self._downloaded_bytes, stream.file_size
        )
        output_path = os.path.join(self.output_dir, f"{output}.{stream.ext}")

        def progress_hook(d):
            if self._cancel:
                return
            if d["status"] == "downloading":
                self._downloaded_bytes += d.get("downloaded_bytes", 0)
                total_bytes = (
                    d.get("total_bytes")
                    or d.get("total_bytes_estimate")
                    or stream.file_size
                    or 1
                )
                progress = self._downloaded_bytes / total_bytes if total_bytes else 0
                progress_callback(
                    DownloadState.DOWNLOADING,
                    min(progress * 0.8, 0.8),
                    self._downloaded_bytes,
                    stream.file_size,
                )

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
        progress_callback: Callable[[DownloadState, float, int, Optional[int]], None],
    ):
        if self._cancel:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            progress_callback(DownloadState.CANCELED, 0, self._downloaded_bytes, None)
            return

        progress_callback(DownloadState.MERGING, 0.85, self._downloaded_bytes, None)
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
        progress_callback: Callable[[DownloadState, float, int, Optional[int]], None],
    ):
        if self._cancel:
            if os.path.exists(input_path):
                os.remove(input_path)
            progress_callback(DownloadState.CANCELED, 0, self._downloaded_bytes, None)
            return

        progress_callback(DownloadState.CONVERTING, 0.9, self._downloaded_bytes, None)
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
        progress_callback: Callable[[DownloadState, float, int, Optional[int]], None],
    ):
        if self._cancel:
            if os.path.exists(input_path):
                os.remove(input_path)
            progress_callback(DownloadState.CANCELED, 0, self._downloaded_bytes, None)
            return

        progress_callback(DownloadState.CONVERTING, 0.9, self._downloaded_bytes, None)
        try:
            ffmpeg.input(input_path).output(
                output_path, acodec="mp3", loglevel="quiet"
            ).run(overwrite_output=True)
            os.remove(input_path)
        except ffmpeg.Error:
            raise Exception("Failed to convert to MP3")
