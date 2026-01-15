"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_title: str = "Calculator API"
    api_version: str = "1.0.0"
    environment: str = "Staging"  # Staging, Production, Development
    service_name: str = "calculator-api"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 80

    # Debug
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
