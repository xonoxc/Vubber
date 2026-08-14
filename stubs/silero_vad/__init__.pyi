from typing import Any, Callable, Literal

import torch


class OnnxWrapper:
    def __call__(self, x: torch.Tensor, sr: int = 16000) -> torch.Tensor: ...
    def reset_states(self) -> None: ...


class VADIterator:
    def __init__(
        self,
        model: Any,
        threshold: float = 0.5,
        sampling_rate: int = 16000,
        min_silence_duration_ms: int = 100,
        speech_pad_ms: int = 30,
    ) -> None: ...
    def __call__(
        self,
        chunk: torch.Tensor,
        return_seconds: bool = False,
    ) -> dict[str, float] | None: ...
    def reset_states(self) -> None: ...


def load_silero_vad(
    onnx: bool = False,
    opset_version: int = 16,
) -> torch.nn.Module | OnnxWrapper: ...


def read_audio(
    path: str,
    sampling_rate: int = 16000,
) -> torch.Tensor: ...


def save_audio(
    path: str,
    tensor: torch.Tensor,
    sampling_rate: int = 16000,
) -> None: ...


def get_speech_timestamps(
    audio: torch.Tensor,
    model: Any,
    threshold: float = 0.5,
    sampling_rate: int = 16000,
    min_speech_duration_ms: int = 250,
    max_speech_duration_s: float = float("inf"),
    min_silence_duration_ms: int = 100,
    speech_pad_ms: int = 30,
    return_seconds: bool = False,
    time_resolution: int = 1,
    visualize_probs: bool = False,
    progress_tracking_callback: Callable[[float], None] | None = None,
    neg_threshold: float | None = None,
    window_size_samples: int = 512,
    min_silence_at_max_speech: int = 98,
    use_max_poss_sil_at_max_speech: bool = True,
) -> list[dict[str, Any]]: ...


def collect_chunks(
    timestamps: list[dict[str, Any]],
    audio: torch.Tensor,
) -> torch.Tensor: ...


def drop_chunks(
    timestamps: list[dict[str, Any]],
    audio: torch.Tensor,
) -> torch.Tensor: ...