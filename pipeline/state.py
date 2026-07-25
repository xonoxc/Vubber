from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")


class PipelineState:
    def __init__(self) -> None:
        self._artifacts: dict[type, Any] = {}

    def store(self, artifact: Any) -> None:
        self._artifacts[type(artifact)] = artifact

    def get(self, artifact_type: type[T]) -> T:
        result = self._artifacts.get(artifact_type)
        if result is None:
            msg = f"No artifact of type {artifact_type.__name__} in pipeline state"
            raise KeyError(msg)
        return result
