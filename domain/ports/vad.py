from abc import ABC, abstractmethod

from domain.artifacts.audio_artifact import AudioArtifact


class VADer(ABC):
    # Performs voice activity detection on a given audio artifact and returns a list of segments.
    @abstractmethod
    def detect(self, audio: AudioArtifact) -> list[tuple[float, float]]:
        raise NotImplementedError
