from domain.artifacts.audio_artifact import VoiceChunksArtifact
from domain.ports.audio_splitter import AudioSplitter
from stages.stage_interface import Stage
from stages.vad_stage import VADStageOutput


class VoiceSegmentsSplitStage(Stage[VADStageOutput, VoiceChunksArtifact]):
    def __init__(self, audio_splitter: AudioSplitter) -> None:
        self.audio_splitter = audio_splitter

    def execute(self, artifact: VADStageOutput) -> VoiceChunksArtifact:
        audio, voice_timestamps = artifact

        return VoiceChunksArtifact(
            path=self.audio_splitter.split(
                audio,
                speech_reigons=voice_timestamps,
            ),
            regions=voice_timestamps,
        )
