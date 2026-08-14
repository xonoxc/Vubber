from domain.artifacts.audio_artifact import AudioArtifact
from domain.ports.vad import VADer
from providers.vad.vad_provider import SpeechReigon
from stages.stage_interface import Stage

type VADStageOutput = tuple[AudioArtifact, list[SpeechReigon]]


class VADStage(Stage[AudioArtifact, VADStageOutput]):
    def __init__(self, vad: VADer) -> None:
        self.vad = vad

    def execute(self, artifact: AudioArtifact) -> VADStageOutput:
        return artifact, self.vad.detect(artifact)
