"""
CodeCompass Backend — Application Settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Validates settings from environmental values or local .env file.
    """
    APP_NAME: str = "CodeCompass"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    DATABASE_URL: str

    # ── JWT Authentication ──
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Extraction Workspace ──
    WORKSPACE_DIR: str = "workspace"

    # ── Embedding & Vector Storage ──
    CHROMA_PERSIST_DIR: str = "chroma_data"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
