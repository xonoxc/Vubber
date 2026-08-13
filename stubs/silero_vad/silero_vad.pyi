from typing import List, Dict, Union, Any
import torch

class VADIterator:
    def __init__(self, model: Any, threshold: float = 0.5, sampling_rate: int = 16000, min_silence_duration_ms: int = 100, speech_pad_ms: int = 30) -> None: ...
    def __call__(self, chunk: torch.Tensor, return_seconds: bool = False) -> Union[Dict[str, float], None]: ...
    def reset_states(self) -> None: ...

def load_silero_vad(onnx: bool = False) -> torch.nn.Module: ...

def read_audio(path: str, sampling_rate: int = 16000) -> torch.Tensor: ...

def save_audio(path: str, tensor: torch.Tensor, sampling_rate: int = 16000) -> None: ...

def get_speech_timestamps(
    audio: torch.Tensor,
    model: torch.nn.Module,
    threshold: float = 0.5,
    sampling_rate: int = 16000,
    min_speech_duration_ms: int = 250,
    max_speech_duration_s: float = float('inf'),
    min_silence_duration_ms: int = 100,
    window_size_samples: int = 512,
    speech_pad_ms: int = 30,
    return_seconds: bool = False,
    progress_bar: bool = False
) -> List[Dict[str, int]]: ...

def collect_chunks(timestamps: List[Dict[str, int]], audio: torch.Tensor) -> torch.Tensor: ...
