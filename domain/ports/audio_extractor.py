from abc import ABC, abstractmethod

from domain.artifacts.audio_artifact import AudioArtifact
from domain.artifacts.video_artifact import VideoArtifact


class AudioExtractor(ABC):
    @abstractmethod
    def extract(self, video: VideoArtifact) -> AudioArtifact:
        raise NotImplementedError
