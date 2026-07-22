from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from groq import Groq
from pydantic import BaseModel

from domain.artifacts.localized_transcript import (
    LocalizedTranscriptArtifact,
    LocalizedTranscriptSegment,
)
from domain.constants import LOCALIZED_DIR
from domain.ports.translator import Translator
from utils.logging import get_logger

if TYPE_CHECKING:
    from domain.artifacts.transcript import TranscriptArtifact, TranscriptSegment

log = get_logger()


class TranslationError(Exception):
    """Raised when translation fails."""


_TRANSLATION_PROMPT = Path(__file__).resolve().parents[2] / "domain" / "system_prompts" / "translation.xml"
_BATCH_SIZE = 50


class _TranslationResponse(BaseModel):
    segments: list[LocalizedTranscriptSegment]


class GroqTranslator(Translator):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
        target_language: str = "English",
    ) -> None:
        self._client = Groq(api_key=api_key)
        self._model = model
        self._target_language = target_language

    def translate(self, transcript: TranscriptArtifact) -> LocalizedTranscriptArtifact:
        try:
            all_segments: list[LocalizedTranscriptSegment] = []
            segments = transcript.segments
            total_batches = (len(segments) + _BATCH_SIZE - 1) // _BATCH_SIZE

            for i in range(0, len(segments), _BATCH_SIZE):
                batch_num = i // _BATCH_SIZE + 1
                batch = segments[i : i + _BATCH_SIZE]

                log.info(
                    "translation.batch.start",
                    batch=f"{batch_num}/{total_batches}",
                    segments=len(batch),
                )

                translated = self._translate_batch(transcript.language, batch)
                all_segments.extend(translated)

                log.info(
                    "translation.batch.done",
                    batch=f"{batch_num}/{total_batches}",
                    segments=len(translated),
                )

            LOCALIZED_DIR.mkdir(parents=True, exist_ok=True)
            output_path = LOCALIZED_DIR / f"{transcript.language}_{self._target_language}.json"

            artifact = LocalizedTranscriptArtifact(
                path=output_path,
                source_language=transcript.language,
                target_language=self._target_language,
                segments=all_segments,
            )

            output_path.write_text(
                json.dumps(asdict(artifact), indent=2, default=str),
            )

            return artifact
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(
                f"Translation failed: {exc}",
            ) from exc

    def _translate_batch(
        self,
        language: str,
        batch: list[TranscriptSegment],
    ) -> list[LocalizedTranscriptSegment]:
        user_message = json.dumps(
            {
                "language": language,
                "segments": [
                    {
                        "start": s.start,
                        "end": s.end,
                        "text": s.text,
                    }
                    for s in batch
                ],
            },
            ensure_ascii=False,
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _TRANSLATION_PROMPT.read_text()},
                {
                    "role": "user",
                    "content": f"Translate the following transcript into {self._target_language}.\n\n{user_message}",
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "translation_response",
                    "schema": _TranslationResponse.model_json_schema(),
                },
            },
            temperature=0,
            max_tokens=8192,
        )

        raw = response.choices[0].message.content or ""

        try:
            parsed = _TranslationResponse.model_validate_json(
                raw,
            )
        except Exception as exc:
            raise TranslationError(f"Failed to validate LLM response: {exc}") from exc

        if len(parsed.segments) != len(batch):
            raise TranslationError(
                f"Expected {len(batch)} segments, got {len(parsed.segments)}",
            )

        return [
            LocalizedTranscriptSegment(
                start=original.start,
                end=original.end,
                original_text=original.text,
                localized_text=segment.localized_text,
            )
            for original, segment in zip(batch, parsed.segments, strict=True)
        ]
