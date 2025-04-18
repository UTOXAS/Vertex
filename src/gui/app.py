import customtkinter as ctk
import threading
from typing import Optional
from .styles import configure_theme, get_neobrutalist_styles
from .widgets import (
    UrlInputWidget,
    VideoInfoWidget,
    DownloadOptionsWidget,
    ProgressWidget,
)
from backend.downloader import Downloader
from backend.models import DownloadOption, DownloadState


class VertexApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Vertex")
        self.root.geometry("600x800")
        configure_theme()
        self.styles = get_neobrutalist_styles()

        self.downloader = Downloader()
        self.selected_option: Optional[DownloadOption] = None

        self._setup_gui()

    def _setup_gui(self):
        self.root.configure(fg_color=self.styles["bg_color"])

        # Title
        title_label = ctk.CTkLabel(
            self.root,
            text="Vertex",
            font=self.styles["font_title"],
            text_color=self.styles["text_color"],
        )
        title_label.pack(pady=20)

        # URL Input
        self.url_input = UrlInputWidget(self.root, self._fetch_video_info, self.styles)
        self.url_input.pack(pady=10, padx=20, fill="x")

        # Video Info
        self.video_info = VideoInfoWidget(self.root, self.styles)
        self.video_info.pack(pady=10, padx=20, fill="x")

        # Download Options
        self.download_options = DownloadOptionsWidget(
            self.root, self._on_option_selected, self.styles
        )
        self.download_options.pack(pady=10, padx=20, fill="x")

        # Progress
        self.progress = ProgressWidget(self.root, self._start_download, self.styles)
        self.progress.pack(pady=10, padx=20, fill="x")

    def _fetch_video_info(self, url: str):
        if not url:
            return

        self.progress.reset()
        threading.Thread(
            target=self._fetch_info_thread, args=(url,), daemon=True
        ).start()

    def _fetch_info_thread(self, url: str):
        try:
            info = self.downloader.get_video_info(url)
            self.root.after(0, lambda: self._display_info(info))
        except Exception as e:
            self.root.after(
                0, lambda: self.progress.update_progress(DownloadState.FINISHED, 0)
            )

    def _display_info(self, info: dict):
        self.video_info.display_info(info["title"], info["thumbnail"])
        self.download_options.display_options(info["options"])

    def _on_option_selected(self, option: DownloadOption):
        self.selected_option = option

    def _start_download(self):
        if not self.selected_option:
            return

        self.progress.reset()
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        try:
            self.downloader.download(
                self.selected_option,
                lambda state, progress: self.root.after(
                    0, lambda: self.progress.update_progress(state, progress)
                ),
            )
        except Exception:
            self.root.after(
                0, lambda: self.progress.update_progress(DownloadState.FINISHED, 0)
            )

    def run(self):
        self.root.mainloop()
