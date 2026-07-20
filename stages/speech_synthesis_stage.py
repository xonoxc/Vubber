from domain.artifacts.localized_transcript import LocalizedTranscriptArtifact
from domain.artifacts.speech_artifact import SpeechArtifact
from domain.ports.speech_synthesizer import SpeechSynthesizer
from stages.stage_interface import Stage


class SpeechSynthesisStage(Stage[LocalizedTranscriptArtifact, SpeechArtifact]):
    def __init__(self, speech_synthesizer: SpeechSynthesizer) -> None:
        self._speech_synthesizer = speech_synthesizer

    def execute(self, artifact: LocalizedTranscriptArtifact) -> SpeechArtifact:
        return self._speech_synthesizer.synthesize(artifact)
