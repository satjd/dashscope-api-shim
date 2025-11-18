"""Configuration management for DashScope API Shim."""

import json
from typing import Dict, List, Optional

from pydantic import field_validator
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

    # Bailian App Configuration
    # Option 1: Single app (legacy, for backward compatibility)
    BAILIAN_APP_ID: Optional[str] = None

    # Option 2: Multiple apps mapping (model_name -> app_id)
    # Format: JSON string like '{"qwen-plus": "app-id-1", "qwen-turbo": "app-id-2"}'
    BAILIAN_APP_MAPPING: Optional[str] = None

    BAILIAN_REASONING_DELTA_MAX: int = 180  # Max length for reasoning delta in streaming

    @field_validator('BAILIAN_APP_MAPPING', mode='before')
    @classmethod
    def parse_app_mapping(cls, v: Optional[str]) -> Optional[str]:
        """Validate that BAILIAN_APP_MAPPING is valid JSON if provided."""
        if v is None:
            return v
        try:
            # Try to parse as JSON to validate format
            parsed = json.loads(v)
            if not isinstance(parsed, dict):
                raise ValueError("BAILIAN_APP_MAPPING must be a JSON object")
            # Validate all values are strings
            for key, value in parsed.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError("BAILIAN_APP_MAPPING keys and values must be strings")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"BAILIAN_APP_MAPPING must be valid JSON: {e}")

    def get_app_mapping(self) -> Dict[str, str]:
        """
        Get the app ID mapping as a dictionary.

        Returns dict of model_name -> app_id.
        Falls back to legacy BAILIAN_APP_ID if BAILIAN_APP_MAPPING not set.
        """
        if self.BAILIAN_APP_MAPPING:
            return json.loads(self.BAILIAN_APP_MAPPING)
        elif self.BAILIAN_APP_ID:
            # Legacy mode: single app ID
            return {f"bailian-app-{self.BAILIAN_APP_ID}": self.BAILIAN_APP_ID}
        else:
            raise ValueError("Either BAILIAN_APP_MAPPING or BAILIAN_APP_ID must be set")

    def get_app_id_for_model(self, model_name: str) -> Optional[str]:
        """
        Get app ID for a given model name.

        Args:
            model_name: The model name from the request

        Returns:
            The corresponding app ID, or None if not found
        """
        mapping = self.get_app_mapping()
        return mapping.get(model_name)

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