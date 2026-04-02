"""Application configuration and environment validation for the agent."""

from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Typed runtime settings loaded from environment variables."""

    google_api_key: str
    tavily_api_key: str
    model_name: str = "gemini-2.5-flash"
    max_iterations: int = 3
    tavily_max_results: int = 5
    log_level: str = "INFO"


def _read_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}. "
                         "Create a .env file from .env.example and set all required keys."
        )

    return value


def _read_int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {name} must be an integer, got: {raw!r}"
        ) from exc

    if parsed < minimum:
        raise ValueError(
            f"Environment variable {name} must be >= {minimum}, got: {parsed}"
        )

    return parsed


def load_settings() -> Settings:
    """Load settings from .env + process env, then validate values."""

    load_dotenv(override=False)

    return Settings(
        google_api_key=_read_required_env("GOOGLE_API_KEY"),
        tavily_api_key=_read_required_env("TAVILY_API_KEY"),
        model_name=os.getenv("MODEL_NAME", "gemini-2.5-flash"),
        max_iterations=_read_int_env("MAX_ITERATIONS", default=3, minimum=1),
        tavily_max_results=_read_int_env("TAVILY_MAX_RESULTS", default=5, minimum=1),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
