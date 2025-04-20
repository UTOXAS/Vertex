import customtkinter as ctk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from typing import Callable, List
from backend.models import DownloadOption, DownloadState


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
        self.option_var = ctk.StringVar(value="-1")
        self.options: List[DownloadOption] = []
        self.option_frames: List[ctk.CTkFrame] = []

        # Scrollable frame for options
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
            scrollbar_button_color=styles["accent_color"],
            scrollbar_button_hover_color="#4682B4",
        )
        self.scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

    def display_options(self, options: List[DownloadOption]):
        # Clear existing options
        for frame in self.option_frames:
            frame.destroy()
        self.option_frames.clear()
        self.options = options
        self.option_var.set("-1")

        # Create newオプション frames
        for idx, option in enumerate(options):
            frame = ctk.CTkFrame(
                self.scrollable_frame,
                fg_color=self.styles["fg_color"],
                border_color=self.styles["border_color"],
                border_width=1,
            )
            frame.pack(fill="x", padx=10, pady=5, anchor="n")

            # Radio button
            rb = ctk.CTkRadioButton(
                frame,
                text="",
                variable=self.option_var,
                value=str(idx),
                command=lambda: self._on_option_selected(),
            )
            rb.pack(side="left", padx=5)

            # Thumbnail
            try:
                response = requests.get(option.thumbnail)
                img_data = BytesIO(response.content)
                img = Image.open(img_data).resize((100, 56), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                thumb_label = ctk.CTkLabel(frame, image=photo, text="")
                thumb_label.image = photo  # Keep reference
                thumb_label.pack(side="left", padx=5)
            except Exception:
                thumb_label = ctk.CTkLabel(
                    frame, text="No Thumbnail", font=self.styles["font_label"]
                )
                thumb_label.pack(side="left", padx=5)

            # Details frame
            details = ctk.CTkFrame(frame, fg_color=self.styles["fg_color"])
            details.pack(side="left", fill="x", expand=True)

            # Title
            title_label = ctk.CTkLabel(
                details,
                text=(
                    option.title[:50] + "..."
                    if len(option.title) > 50
                    else option.title
                ),
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
            )
            title_label.pack(anchor="w")

            # Quality
            quality_label = ctk.CTkLabel(
                details,
                text=option.label,
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
            )
            quality_label.pack(anchor="w")

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

            # Processing Requirements
            processing = []
            if option.requires_conversion:
                processing.append("CONVERTING")
            if option.requires_merging:
                processing.append("MERGING")
            processing_text = (
                f"Requires: {', '.join(processing) if processing else 'None'}"
            )
            processing_label = ctk.CTkLabel(
                details,
                text=processing_text,
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
            )
            processing_label.pack(anchor="w")

            self.option_frames.append(frame)

        if options:
            self.option_var.set("0")
            self._on_option_selected()

    def _on_option_selected(self):
        idx = int(self.option_var.get()) if self.option_var.get() != "-1" else -1
        if idx >= 0:
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

        self.progress_bar = ctk.CTkProgressBar(
            self, width=300, progress_color=self.styles["accent_color"]
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

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

    def update_progress(self, state: DownloadState, progress: float):
        self.status_label.configure(text=f"Status: {state.value}")
        self.progress_bar.set(max(0.0, min(1.0, progress)))

    def reset(self):
        self.status_label.configure(text="Status: Idle")
        self.progress_bar.set(0)
