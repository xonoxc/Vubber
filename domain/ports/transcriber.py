from abc import ABC, abstractmethod

from domain.artifacts.audio_artifact import VoiceChunksArtifact
from domain.artifacts.transcript import TranscriptArtifact


class Transcriber(ABC):
    @abstractmethod
    def transcribe(
        self,
        artifacts: VoiceChunksArtifact,
    ) -> TranscriptArtifact:
        raise NotImplementedError
