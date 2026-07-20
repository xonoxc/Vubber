from domain.artifacts.localized_transcript import LocalizedTranscriptArtifact
from domain.artifacts.transcript import TranscriptArtifact
from domain.ports.translator import Translator
from stages.stage_interface import Stage


class TranslationStage(Stage[TranscriptArtifact, LocalizedTranscriptArtifact]):
    def __init__(self, translator: Translator) -> None:
        self._translator = translator

    def execute(self, artifact: TranscriptArtifact) -> LocalizedTranscriptArtifact:
        return self._translator.translate(artifact)
