from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class VideoArtifact:
    path: Path
