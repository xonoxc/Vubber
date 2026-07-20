from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadError

from domain.artifacts.url import YoutubeURL
from domain.artifacts.video_artifact import VideoArtifact
from providers.yt_downloader import YtDlpDownloader

if TYPE_CHECKING:
    from pathlib import Path


def _make_url(url: str) -> YoutubeURL:
    return YoutubeURL.model_validate({"value": url})


@pytest.fixture()
def downloader(tmp_path: Path) -> YtDlpDownloader:
    return YtDlpDownloader(output_dir=tmp_path)


@pytest.fixture()
def mock_ydl() -> MagicMock:
    mock = MagicMock()
    mock.extract_info.return_value = {"id": "abc123", "ext": "mp4"}
    return mock


class TestYtDlpDownloader:
    @patch("providers.yt_downloader.YoutubeDL")
    def test_download_returns_video_artifact(
        self,
        mock_cls: MagicMock,
        tmp_path: Path,
        mock_ydl: MagicMock,
    ) -> None:
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        downloader = YtDlpDownloader(output_dir=tmp_path)
        video_file = tmp_path / "abc123.mp4"
        video_file.touch()

        url = _make_url("https://www.youtube.com/watch?v=abc123")
        result = downloader.download(url)

        assert isinstance(result, VideoArtifact)
        assert result.path == video_file

    @patch("providers.yt_downloader.YoutubeDL")
    def test_download_passes_correct_options(
        self,
        mock_cls: MagicMock,
        tmp_path: Path,
        mock_ydl: MagicMock,
    ) -> None:
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        downloader = YtDlpDownloader(output_dir=tmp_path)
        video_file = tmp_path / "abc123.mp4"
        video_file.touch()

        url = _make_url("https://www.youtube.com/watch?v=abc123")
        downloader.download(url)

        call_args = mock_cls.call_args
        opts = call_args[0][0]
        assert opts["format"] == "bestvideo+bestaudio/best"
        assert opts["merge_output_format"] == "mp4"
        assert opts["noplaylist"] is True
        assert "%(id)s.%(ext)s" in opts["outtmpl"]

    @patch("providers.yt_downloader.YoutubeDL")
    def test_download_calls_extract_info(
        self,
        mock_cls: MagicMock,
        tmp_path: Path,
        mock_ydl: MagicMock,
    ) -> None:
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        downloader = YtDlpDownloader(output_dir=tmp_path)
        video_file = tmp_path / "abc123.mp4"
        video_file.touch()

        url = _make_url("https://www.youtube.com/watch?v=abc123")
        downloader.download(url)

        mock_ydl.extract_info.assert_called_once_with(
            "https://www.youtube.com/watch?v=abc123",
            download=True,
        )

    @patch("providers.yt_downloader.YoutubeDL")
    def test_download_raises_on_none_info(
        self,
        mock_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = None
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        downloader = YtDlpDownloader(output_dir=tmp_path)
        url = _make_url("https://www.youtube.com/watch?v=abc123")
        with pytest.raises(DownloadError):
            downloader.download(url)

    @patch("providers.yt_downloader.YoutubeDL")
    def test_download_raises_when_file_missing(
        self,
        mock_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"id": "abc123", "ext": "mp4"}
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        downloader = YtDlpDownloader(output_dir=tmp_path)
        url = _make_url("https://www.youtube.com/watch?v=abc123")
        with pytest.raises(FileNotFoundError):
            downloader.download(url)

    @patch("providers.yt_downloader.YoutubeDL")
    def test_download_creates_output_dir(
        self,
        mock_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        output_dir = tmp_path / "nested" / "dir"
        downloader = YtDlpDownloader(output_dir=output_dir)

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"id": "abc123", "ext": "mp4"}
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        video_file = output_dir / "abc123.mp4"
        video_file.touch()

        url = _make_url("https://www.youtube.com/watch?v=abc123")
        result = downloader.download(url)

        assert output_dir.exists()
        assert isinstance(result, VideoArtifact)
