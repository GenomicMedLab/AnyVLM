"""Define app settings."""

from functools import cache

from pydantic import FilePath
from pydantic_settings import BaseSettings, SettingsConfigDict

from anyvlm.schemas.common import ServiceEnvironment


class Settings(BaseSettings):
    """Create app settings

    This is not a singleton, so every new call to this class will re-compute
    configuration settings, defaults, etc.
    """

    model_config = SettingsConfigDict(
        env_prefix="anyvlm_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: ServiceEnvironment = ServiceEnvironment.LOCAL
    service_uri: str = "http://localhost:8080"
    anyvar_uri: str | None = None
    storage_uri: str = "postgresql://postgres@localhost:5432/anyvlm"
    logging_config: FilePath | None = None


@cache
def get_config() -> Settings:
    """Get runtime configuration.

    This function is cached, so the config object only gets created/calculated once.

    :return: Settings instance
    """
    return Settings()
