from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel


class LocalizedTranscriptSegment(BaseModel):
    start: float
    end: float
    original_text: str = ""
    localized_text: str = ""


@dataclass(slots=True)
class LocalizedTranscriptArtifact:
    path: Path
    source_language: str
    target_language: str
    segments: list[LocalizedTranscriptSegment]
