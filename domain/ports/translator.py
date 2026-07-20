from abc import ABC, abstractmethod

from domain.artifacts.localized_transcript import LocalizedTranscriptArtifact
from domain.artifacts.transcript import TranscriptArtifact


class Translator(ABC):
    @abstractmethod
    def translate(self, transcript: TranscriptArtifact) -> LocalizedTranscriptArtifact:
        raise NotImplementedError
