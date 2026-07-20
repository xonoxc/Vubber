from pydantic import AnyHttpUrl, BaseModel, HttpUrl, field_validator


class YoutubeURL(BaseModel):
    value: HttpUrl

    @field_validator("url")
    @classmethod
    def validate_youtube(cls, value: AnyHttpUrl):
        host = value.host or ""

        allowed = {"youtube.com", "www.youtube.com", "m.youtube.com"}

        if host not in allowed:
            raise ValueError("Only YouTube URLs are supported.")

        return value
