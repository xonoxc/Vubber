from domain.artifacts.audio_artifact import AudioArtifact
from domain.artifacts.video_artifact import VideoArtifact
from domain.ports.audio_extractor import AudioExtractor
from stages.stage_interface import Stage


class AudioExtractionStage(Stage[VideoArtifact, AudioArtifact]):
    def __init__(self, extractor: AudioExtractor) -> None:
        self._extractor = extractor

    def execute(
        self,
        artifact: VideoArtifact,
    ) -> AudioArtifact:
        return self._extractor.extract(artifact)
