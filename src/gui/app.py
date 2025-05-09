import customtkinter as ctk
import threading
from typing import Optional, List, Tuple
from .styles import configure_theme, get_neobrutalist_styles
from .widgets import (
    UrlInputWidget,
    DownloadOptionsWidget,
    DownloadsWidget,
)
from vertex_downloader.downloader import Downloader
from vertex_downloader.models import DownloadOption, DownloadState


class VertexApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Vertex")
        self.root.geometry("600x800")
        configure_theme()
        self.styles = get_neobrutalist_styles()

        self.downloader = Downloader()
        self.selected_option: Optional[DownloadOption] = None
        self.downloads: List[
            Tuple[DownloadOption, Downloader, threading.Thread, List]
        ] = []
        self.download_id_counter = 0

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

        # Tabview for navigation
        self.tabview = ctk.CTkTabview(
            self.root,
            fg_color=self.styles["fg_color"],
            border_color=self.styles["border_color"],
            border_width=2,
            segmented_button_fg_color=self.styles["accent_color"],
            segmented_button_selected_color=self.styles["highlight_color"],
            segmented_button_selected_hover_color=self.styles["switch_hover_color"],
            segmented_button_unselected_color=self.styles["fg_color"],
            segmented_button_unselected_hover_color=self.styles["switch_color"],
            text_color=self.styles["text_color"],
        )
        self.tabview.pack(pady=5, padx=20, fill="both", expand=True)

        # Download Tab
        self.download_tab = self.tabview.add("Download")
        self.download_frame = ctk.CTkFrame(
            self.download_tab,
            fg_color=self.styles["fg_color"],
        )
        self.download_frame.pack(fill="both", expand=True)

        # URL Input
        self.url_input = UrlInputWidget(
            self.download_frame, self._fetch_video_info, self.styles
        )
        self.url_input.pack(pady=10, padx=20, fill="x")

        # Loading Indicator
        self.loading_label = ctk.CTkLabel(
            self.download_frame,
            text="",
            font=self.styles["font_label"],
            text_color=self.styles["text_color"],
        )
        self.loading_label.pack(pady=5)

        # Download Options
        self.download_options = DownloadOptionsWidget(
            self.download_frame, self._start_download, self.styles
        )
        self.download_options.pack(pady=10, padx=20, fill="both", expand=True)

        # Downloads Tab
        self.downloads_tab = self.tabview.add("Active Downloads")
        self.downloads_frame = ctk.CTkFrame(
            self.downloads_tab,
            fg_color=self.styles["fg_color"],
        )
        self.downloads_frame.pack(fill="both", expand=True)

        # Downloads List
        self.downloads_widget = DownloadsWidget(
            self.downloads_frame, self._cancel_download, self.styles
        )
        self.downloads_widget.pack(pady=10, padx=20, fill="both", expand=True)

    def _fetch_video_info(self, url: str):
        if not url:
            return

        self.loading_label.configure(text="Loading video info...")
        threading.Thread(
            target=self._fetch_info_thread, args=(url,), daemon=True
        ).start()

    def _fetch_info_thread(self, url: str):
        try:
            videos = self.downloader.get_video_info(url)
            self.root.after(0, lambda: self._display_info(videos))
        except Exception:
            self.root.after(0, lambda: self._display_error())
        finally:
            self.root.after(0, lambda: self.loading_label.configure(text=""))

    def _display_info(self, videos: list):
        options = [option for video in videos for option in video["options"]]
        self.download_options.display_options(options)

    def _display_error(self):
        self.loading_label.configure(text="Failed to load video info")

    def _start_download(self, option: DownloadOption):
        if not option:
            return

        downloader = Downloader()
        download_id = self.download_id_counter
        self.download_id_counter += 1

        frame, status_label, progress_label = self.downloads_widget.add_download(
            option, download_id
        )
        download_thread = threading.Thread(
            target=self._download_thread,
            args=(
                option,
                downloader,
                download_id,
                status_label,
                progress_label,
            ),
            daemon=True,
        )
        self.downloads.append(
            (
                option,
                downloader,
                download_thread,
                [frame, status_label, progress_label],
            )
        )
        download_thread.start()

    def _download_thread(
        self,
        option: DownloadOption,
        downloader: Downloader,
        download_id: int,
        status_label,
        progress_label,
    ):
        try:
            downloader.download(
                option,
                lambda state, progress, downloaded, total: self.root.after(
                    0,
                    lambda: self._update_download_progress(
                        download_id, state, downloaded, total
                    ),
                ),
            )
        except Exception:
            self.root.after(
                0,
                lambda: self.downloads_widget.update_download(
                    download_id, DownloadState.FAILED, 0, None
                ),
            )

    def _update_download_progress(
        self,
        download_id: int,
        state: DownloadState,
        downloaded: int,
        total: Optional[int],
    ):
        self.downloads_widget.update_download(download_id, state, downloaded, total)

    def _cancel_download(self, download_id: int):
        if download_id < len(self.downloads):
            option, downloader, thread, _ = self.downloads[download_id]
            downloader.cancel()
            self.downloads_widget.update_download(
                download_id, DownloadState.CANCELED, 0, option.file_size
            )

    def run(self):
        self.root.mainloop()
