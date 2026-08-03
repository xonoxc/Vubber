import json
import re
import time
from collections.abc import Sequence
from typing import Protocol

from groq import Groq, RateLimitError
from pydantic import BaseModel

from domain.artifacts.localized_transcript import (
    LocalizedTranscriptArtifact,
    LocalizedTranscriptSegment,
)
from domain.artifacts.transcript import TranscriptArtifact, TranscriptSegment
from domain.constants import (
    LOCALIZED_DIR,
    TRANSLATION_MAX_RETRIES,
    TRANSLATION_PROMPT,
    TRANSLATION_RATE_LIMIT_MAX_DELAY_SECONDS,
    TRANSLATION_RATE_LIMIT_MAX_RETRIES,
    TRANSLATION_RETRY_PROMPT,
    TRANSLATiON_BATCH_SIZE,
)
from domain.ports.translator import Translator
from utils.logging import get_logger

log = get_logger()


class TranslationError(Exception):
    """Raised when translation fails."""


class TranslationRateLimitError(TranslationError):
    """Raised when translation keeps failing on rate limits."""


class _HasID(Protocol):
    id: int


class _TranslatedSegment(BaseModel):
    id: int
    localized_text: str


class _TranslationResponse(BaseModel):
    segments: list[_TranslatedSegment]


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
        LOCALIZED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = LOCALIZED_DIR.joinpath(
            f"{transcript.language}_{self._target_language}.json",
        )

        if output_path.exists():
            raw = json.loads(output_path.read_text())
            return LocalizedTranscriptArtifact(
                path=output_path,
                source_language=raw["source_language"],
                target_language=raw["target_language"],
                segments=[
                    LocalizedTranscriptSegment(
                        **s,
                    )
                    for s in raw["segments"]
                ],
            )

        try:
            all_segments: list[LocalizedTranscriptSegment] = []
            segments = transcript.segments
            total_batches = (len(segments) + TRANSLATiON_BATCH_SIZE - 1) // TRANSLATiON_BATCH_SIZE

            for i in range(0, len(segments), TRANSLATiON_BATCH_SIZE):
                batch_num = i // TRANSLATiON_BATCH_SIZE + 1
                batch = segments[i : i + TRANSLATiON_BATCH_SIZE]

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
            output_path = LOCALIZED_DIR.joinpath(f"{transcript.language}_{self._target_language}.json")

            artifact = LocalizedTranscriptArtifact(
                path=output_path,
                source_language=transcript.language,
                target_language=self._target_language,
                segments=all_segments,
            )

            self._check_all_translated(transcript.segments, translated=artifact.segments)

            output_path.write_text(
                json.dumps(
                    {
                        "path": str(output_path),
                        "source_language": artifact.source_language,
                        "target_language": artifact.target_language,
                        "segments": [s.model_dump() for s in artifact.segments],
                    },
                    indent=2,
                ),
            )

            return artifact
        except TranslationError:
            raise
        except Exception as exc:
            raise TranslationError(
                f"Translation failed: {exc}",
            ) from exc

    def _check_all_translated(
        self,
        source: Sequence[_HasID],
        translated: Sequence[_HasID],
    ) -> None:
        source_ids = [segment.id for segment in source]
        translated_ids = [segment.id for segment in translated]

        if source_ids != translated_ids:
            raise TranslationError(
                f"Translation segment mismatch: expected={source_ids}, got={translated_ids}",
            )

    def _request_translation(
        self,
        language: str,
        batch: list[TranscriptSegment],
        retry_context: str | None = None,
        temperature: float = 0.0,
    ) -> list[_TranslatedSegment]:
        user_message = json.dumps(
            {
                "language": language,
                "segments": [{"id": s.id, "text": s.text} for s in batch],
            },
            ensure_ascii=False,
        )

        system_content = TRANSLATION_PROMPT.read_text()
        if retry_context is not None:
            system_content = f"{system_content}\n\n{retry_context}"

        raw = self._create_completion(system_content, user_message, temperature)

        try:
            parsed = _TranslationResponse.model_validate_json(raw)
        except Exception as exc:
            raise TranslationError(
                f"Failed to validate LLM response: {exc}",
            ) from exc

        return parsed.segments

    def _create_completion(
        self,
        system_content: str,
        user_message: str,
        temperature: float,
    ) -> str:
        last_error: RateLimitError | None = None

        for attempt in range(1, TRANSLATION_RATE_LIMIT_MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_content},
                        {
                            "role": "user",
                            "content": f"Translate the following transcript into {self._target_language}.\n\n{user_message}",
                        },
                    ],
                    response_format={
                        "type": "json_object",
                    },
                    temperature=temperature,
                    max_tokens=8192,
                )
                return response.choices[0].message.content or ""
            except RateLimitError as exc:
                last_error = exc
                delay = self._rate_limit_delay(exc)
                if attempt == TRANSLATION_RATE_LIMIT_MAX_RETRIES:
                    break

                log.warning(
                    "translation.rate_limit",
                    attempt=attempt,
                    max_attempts=TRANSLATION_RATE_LIMIT_MAX_RETRIES,
                    delay=delay,
                    error=str(exc),
                )
                time.sleep(delay)

        raise TranslationRateLimitError(
            f"Translation rate limited after {TRANSLATION_RATE_LIMIT_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _rate_limit_delay(exc: RateLimitError) -> float:
        try:
            header = exc.response.headers.get("retry-after")
            if header is not None:
                delay = float(header)
            else:
                message = str(exc)
                match = re.search(
                    r"try again in\s+(?:(\d+)m\s*)?(\d+(?:\.\d+)?)s",
                    message,
                )
                if match is None:
                    delay = 30.0
                else:
                    minutes = float(match.group(1) or 0)
                    seconds = float(match.group(2))
                    delay = minutes * 60 + seconds
        except (AttributeError, TypeError, ValueError):
            delay = 30.0

        return min(delay, TRANSLATION_RATE_LIMIT_MAX_DELAY_SECONDS)

    def _build_localized_segments(
        self,
        source: list[TranscriptSegment],
        translated: list[_TranslatedSegment],
    ) -> list[LocalizedTranscriptSegment]:

        by_id = {segment.id: segment for segment in translated}

        return [
            LocalizedTranscriptSegment(
                id=segment.id,
                start=segment.start,
                end=segment.end,
                original_text=segment.text,
                localized_text=by_id[segment.id].localized_text,
            )
            for segment in source
        ]

    def _translate_batch(
        self,
        language: str,
        batch: list[TranscriptSegment],
    ) -> list[LocalizedTranscriptSegment]:
        last_error: TranslationError | None = None

        for attempt in range(1, TRANSLATION_MAX_RETRIES + 1):
            try:
                retry_context = None
                if last_error is not None:
                    retry_context = TRANSLATION_RETRY_PROMPT.read_text().format(
                        error=str(last_error),
                        expected_ids=[s.id for s in batch],
                    )

                translated = self._request_translation(
                    language,
                    batch,
                    retry_context=retry_context,
                    temperature=0.0 if attempt == 1 else 0.2 * attempt,
                )

                self._check_all_translated(batch, translated)

                return self._build_localized_segments(
                    batch,
                    translated,
                )

            except TranslationRateLimitError:
                raise

            except TranslationError as exc:
                last_error = exc

                log.warning(
                    "translation.retry",
                    attempt=attempt,
                    max_attempts=TRANSLATION_MAX_RETRIES,
                    error=str(exc),
                )

        raise TranslationError(
            f"Translation failed after {TRANSLATION_MAX_RETRIES} attempts: {last_error}",
        )
