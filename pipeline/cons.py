from typing import Any, Self

from stages.stage_interface import Stage


class Pipeline:
    def __init__(self) -> None:
        self._steps: list[Stage[Any, Any]] = []

    def add(self, stage: Stage[Any, Any]) -> Self:
        self._steps.append(stage)
        return self

    def run(self, artifact: object) -> object:
        current = artifact

        for step in self._steps:
            current = step.execute(current)

        return current
