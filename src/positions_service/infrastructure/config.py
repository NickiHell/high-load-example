from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "positions-service"

    database_url: str = Field(
        ...,
        description="Async SQLAlchemy URL, например postgresql+asyncpg://user:pass@host:5432/db",
    )
    database_pool_size: int = Field(default=30, ge=1, le=200)
    database_max_overflow: int = Field(default=60, ge=0, le=500)

    kafka_bootstrap_servers: str = Field(
        ...,
        description="Список брокеров Kafka",
    )
    kafka_topic_positions: str = "positions"

    kafka_client_id: str = "positions-service"

    load_generator_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pydantic-settings reads from env
