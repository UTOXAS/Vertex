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


class VideoInfoWidget(ctk.CTkFrame):
    def __init__(self, master, styles: dict):
        super().__init__(
            master,
            fg_color=styles["fg_color"],
            border_color=styles["border_color"],
            border_width=2,
        )
        self.styles = styles
        self.thumbnail_label = None
        self.title_label = None

    def display_info(self, title: str, thumbnail_url: str):
        if self.thumbnail_label:
            self.thumbnail_label.destroy()
        if self.title_label:
            self.title_label.destroy()

        try:
            response = requests.get(thumbnail_url)
            img_data = BytesIO(response.content)
            img = Image.open(img_data).resize((200, 112), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.thumbnail_label = ctk.CTkLabel(self, image=photo, text="")
            self.thumbnail_label.image = photo  # Keep reference
            self.thumbnail_label.pack(pady=10)
        except Exception:
            self.thumbnail_label = ctk.CTkLabel(
                self, text="No Thumbnail", font=self.styles["font_label"]
            )
            self.thumbnail_label.pack(pady=10)

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        self.title_label.pack(pady=5)


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
        self.option_var = ctk.StringVar()
        self.options: List[DownloadOption] = []
        self.radio_buttons: List[ctk.CTkRadioButton] = []

    def display_options(self, options: List[DownloadOption]):
        for widget in self.radio_buttons:
            widget.destroy()
        self.radio_buttons.clear()
        self.options = options

        for idx, option in enumerate(options):
            rb = ctk.CTkRadioButton(
                self,
                text=option.label,
                variable=self.option_var,
                value=str(idx),
                font=self.styles["font_label"],
                text_color=self.styles["text_color"],
                command=lambda: self._on_option_selected(),
            )
            rb.pack(anchor="w", padx=20, pady=5)
            self.radio_buttons.append(rb)

        if options:
            self.option_var.set("0")
            self._on_option_selected()

    def _on_option_selected(self):
        idx = int(self.option_var.get())
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

        self.progress_bar = ctk.CTkProgressBar(self, width=300)
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
        self.progress_bar.set(progress)

    def reset(self):
        self.status_label.configure(text="Status: Idle")
        self.progress_bar.set(0)
