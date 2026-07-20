from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass(slots=True)
class TranscriptArtifact:
    path: Path
    language: str
    segments: list[TranscriptSegment]
