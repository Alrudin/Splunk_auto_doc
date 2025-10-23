"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    version: str = "0.1.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/splunk_auto_doc",
        description="Database connection URL",
    )

    # Storage
    storage_backend: Literal["local", "s3"] = Field(
        default="local", description="Storage backend type"
    )
    storage_path: str = Field(default="./storage", description="Local storage path")
    s3_bucket: str = Field(default="", description="S3 bucket name")
    s3_endpoint_url: str = Field(default="", description="S3 endpoint URL (for MinIO)")
    aws_access_key_id: str = Field(default="", description="AWS access key ID")
    aws_secret_access_key: str = Field(default="", description="AWS secret access key")

    # API
    api_v1_prefix: str = "/v1"
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"], description="CORS allowed origins"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["text", "json"] = Field(
        default="text", description="Log output format (text or json)"
    )

    # Worker
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL for Celery"
    )
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", description="Celery result backend URL"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
