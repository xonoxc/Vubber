from domain.artifacts.speech_artifact import SpeechArtifact
from domain.artifacts.video_artifact import VideoArtifact
from domain.ports.video_muxer import VideoMuxer
from pipeline.state import PipelineState
from stages.stage_interface import Stage


class MuxStage(Stage[SpeechArtifact, VideoArtifact]):
    def __init__(self, muxer: VideoMuxer, state: PipelineState) -> None:
        self._muxer = muxer
        self._state = state

    def execute(self, artifact: SpeechArtifact) -> VideoArtifact:
        video = self._state.get(VideoArtifact)
        return self._muxer.mux(video, artifact)
