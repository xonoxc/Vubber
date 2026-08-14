from __future__ import annotations

from typing import TYPE_CHECKING

import ffmpeg

from config.constants import OUTPUT_DIR
from domain.artifacts.video_artifact import VideoArtifact
from domain.ports.video_muxer import VideoMuxer

if TYPE_CHECKING:
    from pathlib import Path

    from domain.artifacts.speech_artifact import SpeechArtifact

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class VideoMuxError(Exception):
    """Raised when video muxing fails."""


class FFmpegVideoMuxer(VideoMuxer):
    def __init__(self, output_dir: Path = OUTPUT_DIR) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def mux(
        self,
        video: VideoArtifact,
        speech: SpeechArtifact,
    ) -> VideoArtifact:
        output_path = self._output_dir.joinpath(f"{video.path.stem}_dubbed.mp4")

        if output_path.exists():
            return VideoArtifact(path=output_path)

        video_input = ffmpeg.input(str(video.path))
        speech_input = ffmpeg.input(str(speech.path))

        try:
            (
                ffmpeg.output(
                    video_input.video,
                    speech_input.audio,
                    filename=str(output_path),
                    vcodec="copy",
                    acodec="aac",
                    shortest=None,
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode() if exc.stderr else str(exc)
            raise VideoMuxError(f"FFmpeg mux failed: {stderr}") from exc

        if not output_path.exists():
            raise VideoMuxError(f"Expected output file not found: {output_path}")

        return VideoArtifact(path=output_path)
