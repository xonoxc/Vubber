from domain.artifacts.url import YoutubeURL
from domain.artifacts.video_artifact import VideoArtifact
from domain.ports.downloader import Downloader
from stages.stage_interface import Stage


class DownloadStage(Stage[YoutubeURL, VideoArtifact]):
    def __init__(self, downloader: Downloader) -> None:
        self._downloader = downloader

    def execute(
        self,
        artifact: YoutubeURL,
    ) -> VideoArtifact:
        return self._downloader.download(artifact)
