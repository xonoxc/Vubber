from urllib.parse import parse_qs, urlparse

from pydantic import AnyHttpUrl, BaseModel, HttpUrl, field_validator

VALID_YT_DOMAINS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


class YoutubeURL(BaseModel):
    value: HttpUrl

    @field_validator("value")
    @classmethod
    def validate_youtube(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        host = value.host or ""

        if host not in VALID_YT_DOMAINS:
            raise ValueError("Only YouTube URLs are supported.")

        return value

    @property
    def video_id(self) -> str:
        host = self.value.host or ""
        path = self.value.path or ""

        if host == "youtu.be":
            return path.strip("/")

        parsed = urlparse(url=str(self.value))
        params = parse_qs(
            parsed.query,
        )
        return params["v"][0]
