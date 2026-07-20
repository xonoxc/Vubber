from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from domain.artifacts.video_artifact import VideoArtifact
from domain.ports.downloader import Downloader

if TYPE_CHECKING:
    from yt_dlp import _Params  # type: ignore[reportPrivateUsage]

    from domain.artifacts.url import YoutubeURL


# Downloads a video from a given URL and returns a video artifact.
class YtDlpDownloader(Downloader):
    def __init__(
        self,
        output_dir: Path = Path("artifacts"),
    ) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: YoutubeURL) -> VideoArtifact:
        output_template = str(self._output_dir / "%(id)s.%(ext)s")

        opts: _Params = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "noplaylist": True,
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
