from abc import ABC, abstractmethod
from pathlib import Path


class Downloader(ABC):
    @abstractmethod
    def download(self, url: str, destination: Path) -> None:
        """Download a file from the given URL to the specified destination."""
        pass
