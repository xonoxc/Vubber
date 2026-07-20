from abc import ABC, abstractmethod

from vubber.domain.artifacts.url import YoutubeURL
from vubber.domain.artifacts.video_artifact import VideoArtifact


class Downloader(ABC):
    # Downloads a video from a given URL and returns a video artifact.
    @abstractmethod
    def download(self, url: YoutubeURL) -> VideoArtifact:
        raise NotImplementedError
