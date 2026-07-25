from abc import ABC, abstractmethod

from domain.artifacts.speech_artifact import SpeechArtifact
from domain.artifacts.video_artifact import VideoArtifact


class VideoMuxer(ABC):
    @abstractmethod
    def mux(
        self,
        video: VideoArtifact,
        speech: SpeechArtifact,
    ) -> VideoArtifact:
        raise NotImplementedError
