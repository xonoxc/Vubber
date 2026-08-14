from domain.artifacts.audio_artifact import VoiceChunksArtifact
from domain.artifacts.transcript import TranscriptArtifact
from domain.ports.transcriber import Transcriber
from stages.stage_interface import Stage


class TranscriptionStage(Stage[VoiceChunksArtifact, TranscriptArtifact]):
    def __init__(self, transcriber: Transcriber) -> None:
        self._transcriber = transcriber

    def execute(self, artifact: VoiceChunksArtifact) -> TranscriptArtifact:
        return self._transcriber.transcribe(artifact)
