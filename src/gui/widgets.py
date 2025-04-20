import customtkinter as ctk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from typing import Callable, List, Optional
from vertex_downloader.models import DownloadOption, DownloadState
import textwrap


def format_size(bytes_size: Optional[int], downloaded: int = 0) -> str:
    """Format size in kB or MB, showing downloaded/total if total is known."""
    if bytes_size is None:
        return f"Downloaded: {(downloaded / 1024):.1f} kB"

    total_kb = bytes_size / 1024
    downloaded_kb = downloaded / 1024
    if total_kb > 1024:
        return (
            f"Downloaded: {(downloaded_kb / 1024):.1f} MB / {(total_kb / 1024):.1f} MB"
        )
    return f"Downloaded: {downloaded_kb:.1f} kB / {total_kb:.1f} kB"


class UrlInputWidget(ctk.CTkFrame):
    def __init__(self, master, on_fetch: Callable[[str], None], styles: dict):
        super().__init__(
            master,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
        )
        self.styles = styles

        self.label = ctk.CTkLabel(
            self,
            text="Enter Video URL",
            font=styles["font_label"],
            text_color=styles["text_color"],
        )
        self.label.pack(pady=10)

        self.entry = ctk.CTkEntry(
            self, width=400, font=styles["font_label"], placeholder_text="https://..."
        )
        self.entry.pack(pady=5, padx=20)

        self.button = ctk.CTkButton(
            self,
            text="Get Video Info",
            command=lambda: on_fetch(self.entry.get()),
            font=styles["font_button"],
            fg_color=styles["accent_color"],
            text_color=styles["text_color"],
            hover_color="#4682B4",
        )
        self.button.pack(pady=10)

    def get_url(self) -> str:
        return self.entry.get()


class DownloadOptionsWidget(ctk.CTkFrame):
    def __init__(
        self, master, on_select: Callable[[DownloadOption], None], styles: dict
    ):
        super().__init__(
            master,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
        )
        self.styles = styles
        self.on_select = on_select
        self.options: List[DownloadOption] = []
        self.selected_frame: Optional[ctk.CTkFrame] = None

        # Tabview for Video+Sound and Audio Only
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            segmented_button_fg_color=styles["accent_color"],
            segmented_button_selected_color=styles["highlight_color"],
            segmented_button_selected_hover_color=styles["switch_hover_color"],
            segmented_button_unselected_color=styles["fg_color"],
            segmented_button_unselected_hover_color=styles["switch_color"],
            text_color=styles["text_color"],
        )
        self.tabview.pack(pady=5, padx=20, fill="both", expand=True)

        # Video+Sound Tab
        self.video_sound_tab = self.tabview.add("Video+Sound")
        self.video_sound_frame = ctk.CTkScrollableFrame(
            self.video_sound_tab,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            scrollbar_button_color=styles["accent_color"],
            scrollbar_button_hover_color="#4682B4",
        )
        self.video_sound_frame.pack(pady=5, padx=10, fill="both", expand=True)

        # Audio Only Tab
        self.audio_tab = self.tabview.add("Audio Only")
        self.audio_frame = ctk.CTkScrollableFrame(
            self.audio_tab,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            scrollbar_button_color=styles["accent_color"],
            scrollbar_button_hover_color="#4682B4",
        )
        self.audio_frame.pack(pady=5, padx=10, fill="both", expand=True)

        self.video_sound_option_frames: List[ctk.CTkFrame] = []
        self.audio_option_frames: List[ctk.CTkFrame] = []

    def display_options(self, options: List[DownloadOption]):
        # Clear existing options
        for frame in self.video_sound_option_frames + self.audio_option_frames:
            frame.destroy()
        self.video_sound_option_frames.clear()
        self.audio_option_frames.clear()
        self.options = options
        self.selected_frame = None

        # Filter and sort options
        video_sound_options = [opt for opt in options if opt.video_stream]
        video_sound_options.sort(
            key=lambda opt: (
                opt.quality_key,
                opt.file_size if opt.file_size is not None else float("inf"),
            ),
            reverse=True,
        )
        audio_options = [
            opt for opt in options if opt.audio_stream and not opt.video_stream
        ]
        audio_options.sort(
            key=lambda opt: (
                opt.quality_key,
                opt.file_size if opt.file_size is not None else float("inf"),
            ),
            reverse=True,
        )

        # Display Video+Sound options
        for idx, option in enumerate(video_sound_options):
            frame = self._create_option_frame(option, idx, is_video_sound=True)
            frame.pack(fill="x", padx=10, pady=5, anchor="n")
            self.video_sound_option_frames.append(frame)

        # Display Audio options
        for idx, option in enumerate(audio_options):
            frame = self._create_option_frame(
                option, len(video_sound_options) + idx, is_video_sound=False
            )
            frame.pack(fill="x", padx=10, pady=5, anchor="n")
            self.audio_option_frames.append(frame)

        if options:
            first_frame = (
                self.video_sound_option_frames[0]
                if video_sound_options
                else self.audio_option_frames[0]
            )
            self._select_option(first_frame)

    def _create_option_frame(
        self, option: DownloadOption, idx: int, is_video_sound: bool
    ) -> ctk.CTkFrame:
        parent_frame = self.video_sound_frame if is_video_sound else self.audio_frame
        frame = ctk.CTkFrame(
            parent_frame,
            fg_color=self.styles["fg_color"],
            border_color=self.styles["border_color"],
            border_width=2,
        )
        frame.grid_columnconfigure(1, weight=1)
        frame.bind("<Button-1>", lambda e: self._select_option(frame))
        for child in frame.winfo_children():
            child.bind("<Button-1>", lambda e: self._select_option(frame))

        # Thumbnail
        try:
            response = requests.get(option.thumbnail)
            img_data = BytesIO(response.content)
            img = Image.open(img_data).resize((100, 56), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            thumb_label = ctk.CTkLabel(frame, image=photo, text="")
            thumb_label.image = photo
            thumb_label.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
            thumb_label.bind("<Button-1>", lambda e: self._select_option(frame))
        except Exception:
            thumb_label = ctk.CTkLabel(
                frame, text="No Thumbnail", font=self.styles["font_label"]
            )
            thumb_label.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
            thumb_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # Details frame (horizontal layout)
        details = ctk.CTkFrame(frame, fg_color=self.styles["fg_color"])
        details.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        details.bind("<Button-1>", lambda e: self._select_option(frame))

        # Title (truncated to 20 chars)
        title_text = textwrap.shorten(option.title, width=20, placeholder="...")
        title_label = ctk.CTkLabel(
            details,
            text=title_text,
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        title_label.pack(side="left", padx=5)
        title_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # Quality (truncated to 20 chars)
        quality_text = textwrap.shorten(option.label, width=20, placeholder="...")
        quality_label = ctk.CTkLabel(
            details,
            text=quality_text,
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        quality_label.pack(side="left", padx=5)
        quality_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # File Size
        size_text = (
            f"{option.file_size // 1024 // 1024}MB" if option.file_size else "Unknown"
        )
        size_label = ctk.CTkLabel(
            details,
            text=size_text,
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        size_label.pack(side="left", padx=5)
        size_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # Processing Requirements
        processing = []
        if option.requires_conversion and option.convert_to_standard:
            processing.append("CONVERT")
        if option.requires_merging:
            processing.append("MERGE")
        if processing:
            processing_label = ctk.CTkLabel(
                details,
                text="".join(processing),
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
            )
            processing_label.pack(side="left", padx=5)
            processing_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # Conversion Switch (for non-mp4 combined video or non-mp3 audio)
        if option.requires_conversion:
            switch_label = "MP4" if option.video_stream else "MP3"
            switch = ctk.CTkSwitch(
                details,
                text=switch_label,
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
                onvalue=1,
                offvalue=0,
                command=lambda: self._toggle_conversion(
                    option, switch.get(), is_video_sound
                ),
                fg_color=self.styles["fg_color"],
                progress_color=self.styles["switch_color"],
                button_color=self.styles["switch_color"],
                button_hover_color=self.styles["switch_hover_color"],
            )
            switch.select() if option.convert_to_standard else switch.deselect()
            switch.pack(side="left", padx=5)
            switch.bind("<Button-1>", lambda e: self._select_option(frame))

        return frame

    def _toggle_conversion(
        self, option: DownloadOption, state: int, is_video_sound: bool
    ):
        option.convert_to_standard = bool(state)
        option.output_format = (
            "mp4"
            if option.video_stream and option.convert_to_standard
            else (
                option.video_stream.ext
                if option.video_stream
                else (
                    "mp3"
                    if option.audio_stream and option.convert_to_standard
                    else option.audio_stream.ext
                )
            )
        )
        # Refresh the frame
        idx = self.options.index(option)
        old_frame = (
            self.video_sound_option_frames[idx]
            if is_video_sound and idx < len(self.video_sound_option_frames)
            else self.audio_option_frames[idx - len(self.video_sound_option_frames)]
        )
        old_frame.destroy()
        new_frame = self._create_option_frame(option, idx, is_video_sound)
        new_frame.pack(fill="x", padx=10, pady=5, anchor="n")
        if is_video_sound and idx < len(self.video_sound_option_frames):
            self.video_sound_option_frames[idx] = new_frame
        else:
            self.audio_option_frames[idx - len(self.video_sound_option_frames)] = (
                new_frame
            )
        if self.selected_frame == old_frame:
            self._select_option(new_frame)

    def _select_option(self, frame: ctk.CTkFrame):
        if self.selected_frame:
            self.selected_frame.configure(fg_color=self.styles["fg_color"])
        self.selected_frame = frame
        frame.configure(fg_color=self.styles["highlight_color"])
        idx = (
            self.video_sound_option_frames.index(frame)
            if frame in self.video_sound_option_frames
            else len(self.video_sound_option_frames)
            + self.audio_option_frames.index(frame)
        )
        self.on_select(self.options[idx])


class ProgressWidget(ctk.CTkFrame):
    def __init__(self, master, on_download: Callable[[], None], styles: dict):
        super().__init__(
            master,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
        )
        self.styles = styles
        self.on_download = on_download

        self.status_label = ctk.CTkLabel(
            self,
            text="Status: Idle",
            font=styles["font_label"],
            text_color=styles["text_color"],
        )
        self.status_label.pack(pady=5)

        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=styles["font_label"],
            text_color=styles["text_color"],
        )
        self.progress_label.pack(pady=5)

        self.download_button = ctk.CTkButton(
            self,
            text="Download",
            command=on_download,
            font=styles["font_button"],
            fg_color=styles["accent_color"],
            text_color=styles["text_color"],
            hover_color="#4682B4",
        )
        self.download_button.pack(pady=10)

    def update_progress(
        self,
        state: DownloadState,
        progress: float,
        downloaded: int,
        total: Optional[int],
    ):
        self.status_label.configure(text=f"Status: {state.value}")
        self.progress_label.configure(text=format_size(total, downloaded))

    def reset(self):
        self.status_label.configure(text="Status: Idle")
        self.progress_label.configure(text="")


class DownloadsWidget(ctk.CTkFrame):
    def __init__(self, master, on_cancel: Callable[[int], None], styles: dict):
        super().__init__(
            master,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
        )
        self.styles = styles
        self.on_cancel = on_cancel
        self.download_frames: List[ctk.CTkFrame] = []

        self.label = ctk.CTkLabel(
            self,
            text="Active Downloads",
            font=styles["font_label"],
            text_color=styles["text_color"],
        )
        self.label.pack(pady=5, anchor="w", padx=10)

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            scrollbar_button_color=styles["accent_color"],
            scrollbar_button_hover_color="#4682B4",
        )
        self.scrollable_frame.pack(pady=5, padx=20, fill="both", expand=True)

    def add_download(self, option: DownloadOption, download_id: int):
        frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=self.styles["fg_color"],
            border_color=self.styles["border_color"],
            border_width=2,
        )
        frame.pack(fill="x", padx=10, pady=5, anchor="n")
        frame.grid_columnconfigure(1, weight=1)
        self.download_frames.append(frame)

        # Title
        title_label = ctk.CTkLabel(
            frame,
            text=(
                option.title[:50] + "..." if len(option.title) > 50 else option.title
            ),
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
            wraplength=200,
        )
        title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Status
        status_label = ctk.CTkLabel(
            frame,
            text="Status: Pending",
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        status_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # Progress
        progress_label = ctk.CTkLabel(
            frame,
            text="",
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        progress_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        # Cancel Button
        cancel_button = ctk.CTkButton(
            frame,
            text="Cancel",
            command=lambda: self.on_cancel(download_id),
            font=self.styles["font_button"],
            fg_color=self.styles["cancel_button_color"],
            text_color=self.styles["text_color"],
            hover_color=self.styles["cancel_button_hover"],
            width=80,
        )
        cancel_button.grid(row=0, column=1, rowspan=3, padx=5, pady=5, sticky="e")

        return frame, status_label, progress_label

    def update_download(
        self,
        download_id: int,
        state: DownloadState,
        downloaded: int,
        total: Optional[int],
    ):
        if download_id < len(self.download_frames):
            frame = self.download_frames[download_id]
            status_label = frame.winfo_children()[1]
            progress_label = frame.winfo_children()[2]
            status_label.configure(text=f"Status: {state.value}")
            progress_label.configure(text=format_size(total, downloaded))
            if state in [
                DownloadState.FINISHED,
                DownloadState.CANCELED,
                DownloadState.FAILED,
            ]:
                cancel_button = frame.winfo_children()[3]
                cancel_button.configure(state="disabled")
