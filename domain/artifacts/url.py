from pydantic import AnyHttpUrl, BaseModel, HttpUrl, field_validator


class YoutubeURL(BaseModel):
    value: HttpUrl

    @field_validator("value")
    @classmethod
    def validate_youtube(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        host = value.host or ""

        if host not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            raise ValueError(
                "Only YouTube URLs are supported.",
            )

        return value
