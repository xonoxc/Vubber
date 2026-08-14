from __future__ import annotations

import json
from typing import TYPE_CHECKING

from groq import Groq

from config.constants import TRANSCRIPTS_DIR
from domain.artifacts.transcript import TranscriptArtifact, TranscriptSegment
from domain.ports.transcriber import Transcriber
from utils.logging import get_logger

if TYPE_CHECKING:
    from domain.artifacts.audio_artifact import VoiceChunksArtifact

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

    def transcribe(self, artifacts: VoiceChunksArtifact) -> TranscriptArtifact:
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
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

        segments: list[TranscriptSegment] = []
        language = ""
        for idx, chunk_path in enumerate(chunk_paths):
            if idx >= len(artifacts.regions):
                log.warning("transcription.chunk_out_of_range", idx=idx)
                continue

            start, end = artifacts.regions[idx]

            log.info("transcription.chunk", file=chunk_path.name, start=start, end=end)

            try:
                with open(chunk_path, "rb") as f:
                    response = self._client.audio.transcriptions.create(
                        file=(chunk_path.name, f.read()),
                        model=self._model,
                        response_format="verbose_json",
                    )
            except Exception as exc:
                raise TranscriptionError(
                    f"Transcription failed for {chunk_path.name}: {exc}",
                ) from exc

            language = response.language
            text = response.text.strip()

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
