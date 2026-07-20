from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AudioArtifact:
    path: Path
