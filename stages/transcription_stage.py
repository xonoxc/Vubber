from domain.artifacts.audio_artifact import AudioArtifact
from domain.artifacts.transcript import TranscriptArtifact
from domain.ports.transcriber import Transcriber
from stages.stage_interface import Stage


class TranscriptionStage(Stage[AudioArtifact, TranscriptArtifact]):
    def __init__(self, transcriber: Transcriber) -> None:
        self._transcriber = transcriber

    def execute(self, artifact: AudioArtifact) -> TranscriptArtifact:
        return self._transcriber.transcribe(artifact)
