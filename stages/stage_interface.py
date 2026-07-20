from abc import ABC, abstractmethod


# a stage is a single step in a pipeline
class Stage(ABC):
    # main method to execute the step
    @abstractmethod
    def execute(self, artifact: object) -> object:
        pass
