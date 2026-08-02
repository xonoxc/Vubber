from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator


class TranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str

    @model_validator(mode="after")
    def validate_duration(self) -> Self:
        if self.end <= self.start:
            raise ValueError(
                f"[InvalidTranscriptSegment]end must be greater than start: start={self.start}, end={self.end}",
            )

        return self


@dataclass(slots=True)
class TranscriptArtifact:
    path: Path
    language: str
    segments: list[TranscriptSegment]
