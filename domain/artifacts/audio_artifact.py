from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AudioArtifact:
    path: Path


@dataclass(slots=True)
class VoiceChunksArtifact:
    path: Path
    regions: list[tuple[float, float]]
