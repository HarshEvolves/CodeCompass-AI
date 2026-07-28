"""
CodeCompass Backend — Application Configuration

Uses Pydantic BaseSettings to load config from environment variables
or a .env file automatically.

How it works:
  - Each field maps to an environment variable with the SAME name.
  - If the env var isn't set, it uses the default value here.
  - The .env file is read automatically (if it exists).

Usage anywhere in the app:
  from app.core.config import settings
  print(settings.APP_NAME)  # "CodeCompass"
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings in one place."""

    # ── Application ──
    APP_NAME: str = "CodeCompass"
    DEBUG: bool = False

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ──
    # Which frontend URLs are allowed to call this API.
    # In development, Vite runs on http://localhost:5173
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # ── Database ──
    DATABASE_URL: str

    # Tell Pydantic where to find the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Single shared instance — import this everywhere
settings = Settings()
