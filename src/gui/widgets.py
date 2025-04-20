import customtkinter as ctk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from typing import Callable, List, Optional
from backend.models import DownloadOption, DownloadState


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

        # Combined Video+Audio Options
        self.combined_label = ctk.CTkLabel(
            self,
            text="Combined Video+Audio Options",
            font=styles["font_label"],
            text_color=styles["text_color"],
        )
        self.combined_label.pack(pady=5, anchor="w", padx=10)

        self.combined_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            scrollbar_button_color=styles["accent_color"],
            scrollbar_button_hover_color="#4682B4",
        )
        self.combined_frame.pack(pady=5, padx=20, fill="both", expand=True)

        # Merging Video+Audio Options
        self.merging_label = ctk.CTkLabel(
            self,
            text="Video+Audio (Merging Required)",
            font=styles["font_label"],
            text_color=styles["text_color"],
        )
        self.merging_label.pack(pady=5, anchor="w", padx=10)

        self.merging_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            scrollbar_button_color=styles["accent_color"],
            scrollbar_button_hover_color="#4682B4",
        )
        self.merging_frame.pack(pady=5, padx=20, fill="both", expand=True)

        # Audio Only Options
        self.audio_label = ctk.CTkLabel(
            self,
            text="Audio Only Options",
            font=styles["font_label"],
            text_color=styles["text_color"],
        )
        self.audio_label.pack(pady=5, anchor="w", padx=10)

        self.audio_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            scrollbar_button_color=styles["accent_color"],
            scrollbar_button_hover_color="#4682B4",
        )
        self.audio_frame.pack(pady=5, padx=20, fill="both", expand=True)

        self.combined_option_frames: List[ctk.CTkFrame] = []
        self.merging_option_frames: List[ctk.CTkFrame] = []
        self.audio_option_frames: List[ctk.CTkFrame] = []

    def display_options(self, options: List[DownloadOption]):
        # Clear existing options
        for frame in (
            self.combined_option_frames
            + self.merging_option_frames
            + self.audio_option_frames
        ):
            frame.destroy()
        self.combined_option_frames.clear()
        self.merging_option_frames.clear()
        self.audio_option_frames.clear()
        self.options = options
        self.selected_frame = None

        combined_options = [
            opt
            for opt in options
            if opt.video_stream and not opt.audio_stream and not opt.requires_merging
        ]
        merging_options = [
            opt
            for opt in options
            if opt.video_stream and opt.audio_stream and opt.requires_merging
        ]
        audio_options = [
            opt for opt in options if opt.audio_stream and not opt.video_stream
        ]

        # Display Combined Video+Audio options
        for idx, option in enumerate(combined_options):
            frame = self._create_option_frame(option, idx)
            frame.pack(fill="x", padx=10, pady=5, anchor="n")
            self.combined_option_frames.append(frame)

        # Display Merging Video+Audio options
        for idx, option in enumerate(merging_options):
            frame = self._create_option_frame(option, len(combined_options) + idx)
            frame.pack(fill="x", padx=10, pady=5, anchor="n")
            self.merging_option_frames.append(frame)

        # Display Audio options
        for idx, option in enumerate(audio_options):
            frame = self._create_option_frame(
                option, len(combined_options) + len(merging_options) + idx
            )
            frame.pack(fill="x", padx=10, pady=5, anchor="n")
            self.audio_option_frames.append(frame)

        if options:
            first_frame = (
                self.combined_option_frames[0]
                if combined_options
                else (
                    self.merging_option_frames[0]
                    if merging_options
                    else self.audio_option_frames[0]
                )
            )
            self._select_option(first_frame)

    def _create_option_frame(self, option: DownloadOption, idx: int) -> ctk.CTkFrame:
        parent_frame = (
            self.combined_frame
            if option
            in [
                opt for opt in self.options if opt.video_stream and not opt.audio_stream
            ]
            else (
                self.merging_frame
                if option
                in [
                    opt for opt in self.options if opt.video_stream and opt.audio_stream
                ]
                else self.audio_frame
            )
        )
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

        # Details frame
        details = ctk.CTkFrame(frame, fg_color=self.styles["fg_color"])
        details.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        details.bind("<Button-1>", lambda e: self._select_option(frame))

        # Title
        title_label = ctk.CTkLabel(
            details,
            text=(
                option.title[:50] + "..." if len(option.title) > 50 else option.title
            ),
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
            wraplength=300,
        )
        title_label.pack(anchor="w")
        title_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # Quality
        quality_label = ctk.CTkLabel(
            details,
            text=option.label,
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
            wraplength=300,
        )
        quality_label.pack(anchor="w")
        quality_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # File Size
        size_text = (
            f"Size: {option.file_size // 1024 // 1024} MB"
            if option.file_size
            else "Size: Unknown"
        )
        size_label = ctk.CTkLabel(
            details,
            text=size_text,
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        size_label.pack(anchor="w")
        size_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # Processing Requirements
        processing = []
        if option.requires_conversion and option.convert_to_standard:
            processing.append("CONVERTING")
        if option.requires_merging:
            processing.append("MERGING")
        if processing:
            processing_label = ctk.CTkLabel(
                details,
                text=f"Requires: {', '.join(processing)}",
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
            )
            processing_label.pack(anchor="w")
            processing_label.bind("<Button-1>", lambda e: self._select_option(frame))

        # Conversion Switch (for non-mp4 combined video or non-mp3 audio)
        if option.requires_conversion:
            switch_label = "Convert to MP4" if option.video_stream else "Convert to MP3"
            switch = ctk.CTkSwitch(
                details,
                text=switch_label,
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
                onvalue=1,
                offvalue=0,
                command=lambda: self._toggle_conversion(option, switch.get()),
                fg_color=self.styles["fg_color"],
                progress_color=self.styles["switch_color"],
                button_color=self.styles["switch_color"],
                button_hover_color=self.styles["switch_hover_color"],
            )
            switch.select() if option.convert_to_standard else switch.deselect()
            switch.pack(anchor="w", pady=5)
            switch.bind("<Button-1>", lambda e: self._select_option(frame))

        return frame

    def _toggle_conversion(self, option: DownloadOption, state: int):
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
        # Refresh the frame to update processing requirements
        idx = self.options.index(option)
        old_frame = (
            self.combined_option_frames[idx]
            if idx < len(self.combined_option_frames)
            else (
                self.merging_option_frames[idx - len(self.combined_option_frames)]
                if idx
                < len(self.combined_option_frames) + len(self.merging_option_frames)
                else self.audio_option_frames[
                    idx
                    - len(self.combined_option_frames)
                    - len(self.merging_option_frames)
                ]
            )
        )
        old_frame.destroy()
        new_frame = self._create_option_frame(option, idx)
        new_frame.pack(fill="x", padx=10, pady=5, anchor="n")
        if idx < len(self.combined_option_frames):
            self.combined_option_frames[idx] = new_frame
        elif idx < len(self.combined_option_frames) + len(self.merging_option_frames):
            self.merging_option_frames[idx - len(self.combined_option_frames)] = (
                new_frame
            )
        else:
            self.audio_option_frames[
                idx - len(self.combined_option_frames) - len(self.merging_option_frames)
            ] = new_frame
        if self.selected_frame == old_frame:
            self._select_option(new_frame)

    def _select_option(self, frame: ctk.CTkFrame):
        if self.selected_frame:
            self.selected_frame.configure(fg_color=self.styles["fg_color"])
        self.selected_frame = frame
        frame.configure(fg_color=self.styles["highlight_color"])
        idx = (
            self.combined_option_frames.index(frame)
            if frame in self.combined_option_frames
            else (
                len(self.combined_option_frames)
                + self.merging_option_frames.index(frame)
                if frame in self.merging_option_frames
                else len(self.combined_option_frames)
                + len(self.merging_option_frames)
                + self.audio_option_frames.index(frame)
            )
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
