from __future__ import annotations

import json
from typing import TYPE_CHECKING

from faster_whisper import WhisperModel

from domain.artifacts.transcript import TranscriptArtifact, TranscriptSegment
from domain.constants import TRANSCRIPTS_DIR
from domain.ports.transcriber import Transcriber

if TYPE_CHECKING:
    from domain.artifacts.audio_artifact import AudioArtifact


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
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        return self._model

    def transcribe(self, audio: AudioArtifact) -> TranscriptArtifact:
        try:
            model = self._ensure_model()
            segments_iter, info = model.transcribe(str(audio.path))

            segments = [
                TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                )
                for seg in segments_iter
            ]

            TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
            output_path = TRANSCRIPTS_DIR / f"{audio.path.stem}.json"

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
