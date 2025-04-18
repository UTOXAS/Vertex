import yt_dlp
import ffmpeg
import os
from typing import Callable, List, Optional
from .models import DownloadOption, StreamInfo, DownloadState


class Downloader:
    def __init__(self):
        self.output_dir = "downloads"
        os.makedirs(self.output_dir, exist_ok=True)

    def get_video_info(self, url: str) -> dict:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title", "Unknown Title")
        thumbnail = info.get("thumbnail", "")
        streams = self._parse_streams(info)
        options = self._create_download_options(streams)

        return {"title": title, "thumbnail": thumbnail, "options": options}

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

            streams.append(
                StreamInfo(
                    url=url,
                    format_id=format_id,
                    ext=ext,
                    resolution=resolution,
                    bitrate=str(bitrate) if bitrate else None,
                    is_audio=is_audio,
                )
            )
        return streams

    def _create_download_options(
        self, streams: List[StreamInfo]
    ) -> List[DownloadOption]:
        options = []

        # Video + Audio (combined streams)
        for stream in streams:
            if not stream.is_audio and stream.ext in ["mp4", "webm"]:
                label = f"Video+Audio: {stream.resolution or 'Unknown'} ({stream.ext})"
                options.append(
                    DownloadOption(
                        label=label, video_stream=stream, output_format="mp4"
                    )
                )

        # Video + Audio (separate streams)
        video_streams = [s for s in streams if not s.is_audio]
        audio_streams = [s for s in streams if s.is_audio]
        for video in video_streams:
            for audio in audio_streams:
                label = f"Video: {video.resolution or 'Unknown'} + Audio: {audio.bitrate or 'Unknown'}kbps"
                options.append(
                    DownloadOption(
                        label=label,
                        video_stream=video,
                        audio_stream=audio,
                        output_format="mp4",
                    )
                )

        # Audio Only
        for stream in audio_streams:
            label = f"Audio: {stream.bitrate or 'Unknown'}kbps ({stream.ext})"
            options.append(
                DownloadOption(
                    label=label, audio_stream=WITHstream, output_format="mp3"
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
            f"output_{option.label.replace(':', '_').replace(' ', '_')}.{option.output_format}",
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
                progress = d.get("downloaded_bytes", 0) / d.get("total_bytes", 1)
                progress_callback(DownloadState.DOWNLOADING, min(progress, 0.9))

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
        progress_callback(DownloadState.MERGING, 0.9)
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
        progress_callback(DownloadState.CONVERTING, 0.95)
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
        progress_callback(DownloadState.CONVERTING, 0.95)
        try:
            ffmpeg.input(input_path).output(
                output_path, acodec="mp3", loglevel="quiet"
            ).run(overwrite_output=True)
            os.remove(input_path)
        except ffmpeg.Error:
            raise Exception("Failed to convert to MP3")
