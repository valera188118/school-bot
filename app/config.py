from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_chat_id: int = Field(..., alias="ADMIN_CHAT_ID")
    database_url: str = Field(..., alias="DATABASE_URL")
    school_text: str = Field(..., alias="SCHOOL_TEXT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    telegram_proxy_url: str | None = Field(default=None, alias="TELEGRAM_PROXY_URL")
    start_video_file_id: str | None = Field(default=None, alias="START_VIDEO_FILE_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("school_text", mode="before")
    @classmethod
    def expand_escaped_newlines(cls, value: str) -> str:
        if isinstance(value, str):
            return value.replace("\\n", "\n")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
