from __future__ import annotations

from typing import TYPE_CHECKING

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from domain.artifacts.video_artifact import VideoArtifact
from domain.constants import VIDEOS_DIR
from domain.ports.downloader import Downloader

if TYPE_CHECKING:
    from pathlib import Path

    from yt_dlp import _Params  # type: ignore[reportPrivateUsage]

    from domain.artifacts.url import YoutubeURL


class YtDlpDownloader(Downloader):
    def __init__(
        self,
        output_dir: Path = VIDEOS_DIR,
    ) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: YoutubeURL) -> VideoArtifact:
        output_template = str(self._output_dir / "%(id)s.%(ext)s")

        opts: _Params = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "noplaylist": True,
            "retries": 3,
            "fragment_retries": 3,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            },
        }

        # releasing yt dlp resource after user using "with"
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(str(url.value), download=True)
            if not info:
                raise DownloadError(
                    f"Failed to extract info for {url.value}",
                )

            video_id: str = info.get("id", "")
            video_ext: str = info.get("ext") or "mp4"

        video_path = self._output_dir / f"{video_id}.{video_ext}"
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found at {video_path}")

        return VideoArtifact(path=video_path)
