from __future__ import annotations

import json
from typing import TYPE_CHECKING

from faster_whisper import WhisperModel

from config.constants import TRANSCRIPTS_DIR
from domain.artifacts.transcript import TranscriptArtifact, TranscriptSegment
from domain.ports.transcriber import Transcriber
from utils.logging import get_logger

if TYPE_CHECKING:
    from domain.artifacts.audio_artifact import VoiceChunksArtifact

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

    def transcribe(self, artifacts: VoiceChunksArtifact) -> TranscriptArtifact:
        TRANSCRIPTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path = TRANSCRIPTS_DIR.joinpath(f"{artifacts.path.stem}.json")

        if output_path.exists():
            raw = json.loads(output_path.read_text())
            return TranscriptArtifact(
                path=output_path,
                language=raw["language"],
                segments=[
                    TranscriptSegment(
                        id=idx,
                        start=s["start"],
                        end=s["end"],
                        text=s["text"],
                    )
                    for idx, s in enumerate(raw["segments"])
                ],
            )

        chunk_paths = sorted(
            artifacts.path.glob("*.wav"),
            key=lambda p: int(p.stem.rsplit("_", 1)[-1]),
        )

        try:
            model = self._ensure_model()

            segments: list[TranscriptSegment] = []
            language = ""
            for idx, chunk_path in enumerate(chunk_paths):
                if idx >= len(artifacts.regions):
                    log.warning("transcription.chunk_out_of_range", idx=idx)
                    continue

                start, end = artifacts.regions[idx]

                log.info(
                    "transcription.chunk",
                    file=chunk_path.name,
                    start=start,
                    end=end,
                )

                segments_iter, info = model.transcribe(
                    str(chunk_path),
                )

                text = " ".join(seg.text.strip() for seg in segments_iter).strip()

                language = info.language

                if text:
                    segments.append(
                        TranscriptSegment(id=idx, start=start, end=end, text=text),
                    )

            log.info("transcription.done", language=language, segments=len(segments))

            artifact = TranscriptArtifact(
                path=output_path,
                language=language,
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

