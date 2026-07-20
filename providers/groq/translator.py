from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, cast

from groq import Groq

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


_SYSTEM_PROMPT = """\
You are a professional dubbing translator. Your job is to localize dialogue for natural spoken English.

<rules>
- Translate into natural conversational English.
- Preserve the meaning and emotion of each line.
- Keep sentences concise and suitable for spoken delivery.
- Keep approximately the same speaking duration as the original.
- Preserve timestamps exactly. Do not change start or end times.
- Preserve segment ordering. Do not merge or split segments.
- Do not omit any segment.
</rules>

<output_format>
Return ONLY valid JSON. No markdown, no code fences, no explanations.
The output MUST match this exact structure:

{
  "segments": [
    {
      "start": 0.0,
      "end": 1.9,
      "localized_text": "Hello everyone."
    }
  ]
}

Each segment MUST contain:
- "start" (number) — copied exactly from input
- "end" (number) — copied exactly from input
- "localized_text" (string) — your translation

Do NOT use any other key names. Do NOT add extra fields.
</output_format>
"""

_BATCH_SIZE = 50


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
                    {"start": s.start, "end": s.end, "text": s.text}
                    for s in batch
                ],
            },
            ensure_ascii=False,
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Translate the following transcript into "
                        f"{self._target_language}.\n\n{user_message}"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=8192,
        )

        raw = response.choices[0].message.content or ""
        data = self._parse_response(raw)
        return self._build_segments(batch, data)

    def _parse_response(self, raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            parsed: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise TranslationError(
                f"Malformed JSON response: {exc}",
            ) from exc

        if "segments" not in parsed:
            raise TranslationError(
                "Response missing 'segments' key",
            )

        if not isinstance(parsed["segments"], list):
            raise TranslationError(
                "'segments' is not a list",
            )

        return parsed

    def _build_segments(
        self,
        batch: list[TranscriptSegment],
        data: dict[str, Any],
    ) -> list[LocalizedTranscriptSegment]:
        translated = data["segments"]

        if len(translated) != len(batch):
            raise TranslationError(
                f"Expected {len(batch)} segments, got {len(translated)}",
            )

        segments: list[LocalizedTranscriptSegment] = []
        for original, tr in zip(batch, translated, strict=True):
            if not isinstance(tr, dict):
                raise TranslationError("Segment is not a dict")

            seg = cast("dict[str, Any]", tr)
            for key in ("start", "end", "localized_text"):
                if key not in seg:
                    raise TranslationError(
                        f"Segment missing '{key}'",
                    )

            segments.append(
                LocalizedTranscriptSegment(
                    start=original.start,
                    end=original.end,
                    original_text=original.text,
                    localized_text=str(seg["localized_text"]),
                ),
            )

        return segments
