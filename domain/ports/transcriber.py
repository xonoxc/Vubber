from abc import ABC, abstractmethod

from domain.artifacts.audio_artifact import AudioArtifact
from domain.artifacts.transcript import TranscriptArtifact


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio: AudioArtifact) -> TranscriptArtifact:
        raise NotImplementedError
