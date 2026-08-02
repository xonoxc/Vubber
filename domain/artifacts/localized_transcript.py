from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator


class LocalizedTranscriptSegment(BaseModel):
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


@dataclass(slots=True)
class LocalizedTranscriptArtifact:
    path: Path
    source_language: str
    target_language: str
    segments: list[LocalizedTranscriptSegment]
