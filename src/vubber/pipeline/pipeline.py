from typing import Self

from vubber.pipeline.stage import Stage


class Pipeline:
    def __init__(self) -> None:
        self._steps: list[Stage] = []

    # adds a new step to the pipeline
    def add(self, stage: Stage) -> Self:
        self._steps.append(stage)
        return self

    # executing each step one at a time sequentially.
    def run(self, artifact: object) -> object:
        current = artifact

        for step in self._steps:
            current = step.execute(current)

        return current
