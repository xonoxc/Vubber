from typing import Any

class ChatCompletionMessage:
    content: str | None

class ChatCompletionChoice:
    message: ChatCompletionMessage

class ChatCompletion:
    choices: list[ChatCompletionChoice]

class ChatCompletionResource:
    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = ...,
        max_tokens: int = ...,
        **kwargs: Any,
    ) -> ChatCompletion: ...

class Chat:
    completions: ChatCompletionResource

class TranscriptionResponse:
    task: str
    language: str
    duration: float
    text: str
    segments: list[dict[str, Any]]

class TranscriptionResource:
    def create(
        self,
        *,
        file: tuple[str, bytes],
        model: str,
        language: str | None = ...,
        response_format: str = ...,
        temperature: float = ...,
        **kwargs: Any,
    ) -> TranscriptionResponse: ...

class Audio:
    transcriptions: TranscriptionResource

class Groq:
    def __init__(
        self,
        *,
        api_key: str | None = ...,
        **kwargs: Any,
    ) -> None: ...
    @property
    def chat(self) -> Chat: ...
    @property
    def audio(self) -> Audio: ...
