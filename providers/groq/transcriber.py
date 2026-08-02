from __future__ import annotations

import json
from typing import TYPE_CHECKING

from groq import Groq

from domain.artifacts.transcript import TranscriptArtifact, TranscriptSegment
from domain.constants import TRANSCRIPTS_DIR
from domain.ports.transcriber import Transcriber
from utils.logging import get_logger

if TYPE_CHECKING:
    from domain.artifacts.audio_artifact import AudioArtifact

log = get_logger()


class TranscriptionError(Exception):
    """Raised when transcription fails."""


class GroqTranscriber(Transcriber):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "whisper-large-v3",
    ) -> None:
        self._client = Groq(api_key=api_key)
        self._model = model

    def transcribe(self, audio: AudioArtifact) -> TranscriptArtifact:
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = TRANSCRIPTS_DIR.joinpath(f"{audio.path.stem}.json")

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

        try:
            log.info("transcription.start", file=audio.path.name, model=self._model)

            with open(audio.path, "rb") as f:
                response = self._client.audio.transcriptions.create(
                    file=(audio.path.name, f.read()),
                    model=self._model,
                    response_format="verbose_json",
                )

            segments = [
                TranscriptSegment(
                    id=idx,
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"],
                )
                for idx, seg in enumerate(response.segments)
            ]

            log.info("transcription.done", language=response.language, segments=len(segments))

            artifact = TranscriptArtifact(
                path=output_path,
                language=response.language,
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
