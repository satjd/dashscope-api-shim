"""Configuration management for DashScope API Shim."""

from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # DashScope/Bailian Configuration
    DASHSCOPE_API_KEY: str
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"

    # Bailian App Configuration (Required)
    BAILIAN_APP_ID: str  # Bailian Application ID is required
    BAILIAN_REASONING_DELTA_MAX: int = 180  # Max length for reasoning delta in streaming

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    WORKERS: int = 1

    # CORS Settings
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Optional OpenAI Configuration (for testing/comparison)
    OPENAI_API_KEY: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # API Authentication
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: List[str] = []

    # Request Timeout
    REQUEST_TIMEOUT: int = 600  # seconds (10 minutes for long-running requests)


# Create global settings instance
settings = Settings()