from __future__ import annotations

import json
from typing import TYPE_CHECKING

from faster_whisper import WhisperModel

from domain.artifacts.transcript import TranscriptArtifact, TranscriptSegment
from domain.constants import TRANSCRIPTS_DIR
from domain.ports.transcriber import Transcriber
from utils.logging import get_logger

if TYPE_CHECKING:
    from domain.artifacts.audio_artifact import AudioArtifact

log = get_logger()


class TranscriptionError(Exception):
    """Raised when transcription fails."""


class FasterWhisperTranscriber(Transcriber):
    def __init__(
        self,
        model: str = "small",
        device: str = "auto",
        compute_type: str = "default",
    ) -> None:
        self._model_size = model
        self._device = device
        self._compute_type = compute_type
        self._model: WhisperModel | None = None

    def _ensure_model(self) -> WhisperModel:
        if self._model is None:
            log.info("transcription.model.loading", model=self._model_size)

            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )

            log.info("transcription.model.loaded", model=self._model_size)
        return self._model

    def transcribe(self, audio: AudioArtifact) -> TranscriptArtifact:
        TRANSCRIPTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path = TRANSCRIPTS_DIR.joinpath(f"{audio.path.stem}.json")

        if output_path.exists():
            raw = json.loads(output_path.read_text())
            return TranscriptArtifact(
                path=output_path,
                language=raw["language"],
                segments=[
                    TranscriptSegment(
                        start=s["start"],
                        end=s["end"],
                        text=s["text"],
                    )
                    for s in raw["segments"]
                ],
            )

        try:
            model = self._ensure_model()
            log.info("transcription.start", file=audio.path.name)
            segments_iter, info = model.transcribe(
                str(audio.path),
            )

            segments = [
                TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                )
                for seg in segments_iter
            ]

            log.info("transcription.done", language=info.language, segments=len(segments))

            TRANSCRIPTS_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )
            output_path = TRANSCRIPTS_DIR.joinpath(f"{audio.path.stem}.json")

            artifact = TranscriptArtifact(
                path=output_path,
                language=info.language,
                segments=segments,
            )

            output_path.write_text(
                json.dumps(
                    {
                        "path": str(artifact.path),
                        "language": artifact.language,
                        "segments": [
                            {
                                "start": s.start,
                                "end": s.end,
                                "text": s.text,
                            }
                            for s in artifact.segments
                        ],
                    },
                    indent=2,
                ),
            )

            return artifact
        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(
                f"Transcription failed: {exc}",
            ) from exc
