"""Core configuration management for The Hive."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # LLM Configuration
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    model_temperature: float = 0.7
    max_tokens: int = 4096

    # Database Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "the_hive"
    postgres_user: str = "hive_user"
    postgres_password: str = "hive_password"

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Vector Store Configuration
    vector_store_type: str = "chroma"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_dir: str = "./data/chroma"

    # Observability Configuration
    langchain_tracing_v2: bool = True
    langchain_api_key: Optional[str] = None
    langchain_project: str = "hive-mvp"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Sandbox Configuration
    sandbox_type: str = "docker"
    docker_network: str = "none"

    # Security
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance.

    Returns:
        Application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
