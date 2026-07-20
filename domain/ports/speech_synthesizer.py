from abc import ABC, abstractmethod

from domain.artifacts.localized_transcript import LocalizedTranscriptArtifact
from domain.artifacts.speech_artifact import SpeechArtifact


class SpeechSynthesizer(ABC):
    @abstractmethod
    def synthesize(
        self,
        transcript: LocalizedTranscriptArtifact,
    ) -> SpeechArtifact:
        raise NotImplementedError
