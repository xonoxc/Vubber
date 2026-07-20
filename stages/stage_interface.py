from abc import ABC, abstractmethod


class Stage[I, O](ABC):
    @abstractmethod
    def execute(self, artifact: I) -> O:
        raise NotImplementedError
