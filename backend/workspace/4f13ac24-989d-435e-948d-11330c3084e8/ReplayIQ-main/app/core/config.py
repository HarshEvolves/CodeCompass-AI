import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings class using Pydantic Settings.
    It automatically reads environment variables or parses the specified .env file.
    """
    PROJECT_NAME: str = "ReplayIQ"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Connection parameters
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Environment Settings
    ENVIRONMENT: str = "development"   # development | staging | production
    DEBUG: bool = True                 # Include stack traces in error responses
    LOG_LEVEL: str = "INFO"            # DEBUG | INFO | WARNING | ERROR | CRITICAL

    # Configuration for setting up .env loading behaviour

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra environment variables not defined here
        extra="ignore"
    )

    @property
    def sql_database_url(self) -> str:
        """
        Dynamically constructs the synchronous SQLAlchemy database URL
        from the loaded Postgres configuration variables.
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

# Instantiate settings to be imported across the application
env = os.getenv("ENVIRONMENT", "development").lower()
env_files = [".env"]
env_specific = f".env.{env}"
if os.path.exists(env_specific):
    env_files.append(env_specific)

settings = Settings(_env_file=tuple(env_files))
