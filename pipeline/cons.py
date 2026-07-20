from typing import Any, Self

from stages.stage_interface import Stage
from utils.logging import get_logger

log = get_logger()


class Pipeline:
    def __init__(self) -> None:
        self._steps: list[Stage[Any, Any]] = []

    def add(self, stage: Stage[Any, Any]) -> Self:
        self._steps.append(stage)
        return self

    def run(self, artifact: object) -> object:
        current = artifact

        for step in self._steps:
            name = type(step).__name__
            log.info("stage.start", stage=name)
            current = step.execute(current)
            log.info("stage.done", stage=name)

        return current
