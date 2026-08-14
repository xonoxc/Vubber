from abc import ABC, abstractmethod
from pathlib import Path

from domain.artifacts.audio_artifact import AudioArtifact
from providers.vad.vad_provider import SpeechReigon


class AudioSplitter(ABC):
    # splits the audio into actual audio parts
    @abstractmethod
    def split(self, audio: AudioArtifact, speech_reigons: list[SpeechReigon]) -> Path:
        raise NotImplementedError
