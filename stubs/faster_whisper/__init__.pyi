from typing import Any

class Segment:
    start: float
    end: float
    text: str

class TranscriptionInfo:
    language: str
    language_probability: float

class WhisperModel:
    def __init__(
        self,
        model_size_or_path: str,
        device: str = ...,
        compute_type: str = ...,
        **kwargs: Any,
    ) -> None: ...
    def transcribe(
        self,
        audio: str,
        **kwargs: Any,
    ) -> tuple[Any, TranscriptionInfo]: ...
