from typing import Any

def input(filename: str, **kwargs: Any) -> Stream: ...

class Stream:
    def output(self, filename: str, **kwargs: Any) -> Stream: ...
    def overwrite_output(self) -> Stream: ...
    def run(
        self,
        capture_stdout: bool = ...,
        capture_stderr: bool = ...,
    ) -> tuple[Any, Any]: ...

class Error(Exception):
    stderr: bytes | None
