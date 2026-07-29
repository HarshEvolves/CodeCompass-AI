"""
CodeCompass Backend — Application Settings
"""
from typing import List, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Validates settings from environmental values or local .env file.
    """
    APP_NAME: str = "CodeCompass"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://code-compass-ai-pi.vercel.app",
    ]
    DATABASE_URL: str

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            # Support JSON lists: e.g. ["http://localhost"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            # Support comma-separated strings: e.g. http://localhost,http://app
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def convert_database_url(cls, v: Any) -> str:
        if isinstance(v, str):
            # Convert standard postgresql:// prefix to asyncpg dialect scheme
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ── JWT Authentication ──
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Extraction Workspace ──
    WORKSPACE_DIR: str = "workspace"
    UPLOAD_DIR: str = "uploads"

    # ── Embedding & Vector Storage ──
    CHROMA_PERSIST_DIR: str = "chroma_data"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── LLM Configuration (RAG) ──
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
