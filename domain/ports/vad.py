from abc import ABC, abstractmethod


class VADer(ABC):
    # Performs voice activity detection on a given audio file and returns a list of segments.
    @abstractmethod
    def detect(self, audio_file_path: str) -> list[tuple[float, float]]:
        raise NotImplementedError
