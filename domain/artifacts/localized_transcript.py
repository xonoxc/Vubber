from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator


class LocalizedTranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    original_text: str = ""
    localized_text: str = ""

    @model_validator(mode="after")
    def validate_duration(self) -> Self:
        if self.end <= self.start:
            raise ValueError(
                f"[InvalidSegment]end must be greater than start: start={self.start}, end={self.end}",
            )

        return self


class LocalizedTranscriptArtifact(BaseModel):
    path: Path
    source_language: str
    target_language: str
    segments: list[LocalizedTranscriptSegment]

    @model_validator(mode="after")
    def validate_segments(self) -> Self:
        if not self.segments:
            raise ValueError("Transcript must contain segments")

        ids = [segment.id for segment in self.segments]

        if len(ids) != len(set(ids)):
            raise ValueError("Segment IDs must be unique")

        for segment in self.segments:
            if not segment.localized_text.strip():
                raise ValueError(f"Segment {segment.id} has empty localized text")

        return self
