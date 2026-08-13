from __future__ import annotations

from typing import TYPE_CHECKING

import ffmpeg

from config.constants import AUDIO_DIR
from domain.artifacts.audio_artifact import AudioArtifact
from domain.ports.audio_extractor import AudioExtractor

if TYPE_CHECKING:
    from pathlib import Path

    from domain.artifacts.video_artifact import VideoArtifact


class AudioExtractionError(Exception):
    # Raised when ffmpeg audio extraction fails.
    pass


class FFmpegAudioExtractor(AudioExtractor):
    def __init__(
        self,
        output_dir: Path = AUDIO_DIR,
    ) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, video: VideoArtifact) -> AudioArtifact:
        stem = video.path.stem
        output_path = self._output_dir.joinpath(f"{stem}.wav")

        if output_path.exists():
            return AudioArtifact(path=output_path)

        try:
            (
                ffmpeg.input(str(video.path))
                .output(
                    str(output_path),
                    vn=None,
                    ac=1,
                    ar=16000,
                    acodec="pcm_s16le",
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode() if exc.stderr else str(exc)
            raise AudioExtractionError(
                f"ffmpeg failed: {stderr}",
            ) from exc

        if not output_path.exists():
            raise AudioExtractionError(
                f"Expected output file not found: {output_path}",
            )

        return AudioArtifact(path=output_path)
