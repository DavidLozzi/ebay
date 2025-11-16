 from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

from dotenv import load_dotenv
from pydantic import BaseModel, Field, HttpUrl, PositiveInt, ValidationError


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


class AppConfig(BaseModel):
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: HttpUrl | None = Field(default=None, alias="OPENAI_API_BASE")
    mcp_endpoint: HttpUrl | None = Field(default=None, alias="MCP_ENDPOINT")
    mcp_api_key: str | None = Field(default=None, alias="MCP_API_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    concurrency_limit: PositiveInt = Field(default=5, alias="CONCURRENCY_LIMIT")

    model_config = {"populate_by_name": True}

    def require(self, fields: Sequence[str]) -> None:
        missing = [field for field in fields if not getattr(self, field)]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


def _load_env_files() -> None:
    env_path = Path(".env")
    load_dotenv(dotenv_path=env_path if env_path.exists() else None, override=False)


REQUIRED_BY_MODE = {
    "organize": ("openai_api_key",),
    "inventory": ("openai_api_key", "mcp_endpoint", "mcp_api_key"),
    "publish": ("mcp_endpoint", "mcp_api_key"),
}


@lru_cache(maxsize=1)
def get_config(required: Iterable[str] | None = None) -> AppConfig:
    _load_env_files()
    try:
        config = AppConfig()  # type: ignore[call-arg]
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc

    if required:
        config.require(tuple(required))
    return config


def get_config_for_mode(mode: str) -> AppConfig:
    requirements = REQUIRED_BY_MODE.get(mode, ())
    return get_config(requirements)