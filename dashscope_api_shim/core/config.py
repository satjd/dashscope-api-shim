"""Configuration management for DashScope API Shim."""

import json
from typing import Any, Dict, List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig:
    """Configuration for a single Bailian app."""

    def __init__(
        self,
        app_id: str,
        enable_thinking: Optional[bool] = None,
        has_thoughts: Optional[bool] = None,
    ):
        self.app_id = app_id
        self.enable_thinking = enable_thinking
        self.has_thoughts = has_thoughts


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

    # Option 2: Multiple apps mapping (model_name -> app_id or app_config)
    # Simple format: '{"model-1": "app-id-1", "model-2": "app-id-2"}'
    # Extended format: '{"model-1": {"app_id": "app-id-1", "enable_thinking": true, "has_thoughts": false}}'
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

            # Validate each entry
            for key, value in parsed.items():
                if not isinstance(key, str):
                    raise ValueError("BAILIAN_APP_MAPPING keys must be strings")

                # Support both string (simple) and object (extended) formats
                if isinstance(value, str):
                    # Simple format: model_name -> app_id
                    continue
                elif isinstance(value, dict):
                    # Extended format: model_name -> {app_id, enable_thinking, has_thoughts}
                    if "app_id" not in value:
                        raise ValueError(f"Extended format for '{key}' must include 'app_id'")
                    if not isinstance(value["app_id"], str):
                        raise ValueError(f"'app_id' for '{key}' must be a string")

                    # Validate optional boolean fields
                    for field in ["enable_thinking", "has_thoughts"]:
                        if field in value and not isinstance(value[field], bool):
                            raise ValueError(f"'{field}' for '{key}' must be a boolean")
                else:
                    raise ValueError(f"BAILIAN_APP_MAPPING value for '{key}' must be string or object")

            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"BAILIAN_APP_MAPPING must be valid JSON: {e}")

    def get_app_mapping(self) -> Dict[str, Union[str, Dict[str, Any]]]:
        """
        Get the raw app mapping as a dictionary.

        Returns dict of model_name -> (app_id str OR app_config dict).
        Falls back to legacy BAILIAN_APP_ID if BAILIAN_APP_MAPPING not set.
        """
        if self.BAILIAN_APP_MAPPING:
            return json.loads(self.BAILIAN_APP_MAPPING)
        elif self.BAILIAN_APP_ID:
            # Legacy mode: single app ID
            return {f"bailian-app-{self.BAILIAN_APP_ID}": self.BAILIAN_APP_ID}
        else:
            raise ValueError("Either BAILIAN_APP_MAPPING or BAILIAN_APP_ID must be set")

    def get_app_config_mapping(self) -> Dict[str, AppConfig]:
        """
        Get the app configuration mapping.

        Returns dict of model_name -> AppConfig object.
        Converts both simple (string) and extended (dict) formats to AppConfig.
        """
        raw_mapping = self.get_app_mapping()
        config_mapping: Dict[str, AppConfig] = {}

        for model_name, value in raw_mapping.items():
            if isinstance(value, str):
                # Simple format: just app_id
                config_mapping[model_name] = AppConfig(app_id=value)
            elif isinstance(value, dict):
                # Extended format: dict with app_id and optional params
                config_mapping[model_name] = AppConfig(
                    app_id=value["app_id"],
                    enable_thinking=value.get("enable_thinking"),
                    has_thoughts=value.get("has_thoughts"),
                )

        return config_mapping

    def get_model_list(self) -> List[str]:
        """
        Get list of available model names.

        Returns:
            List of model names configured in the mapping
        """
        return list(self.get_app_mapping().keys())

    def get_app_id_for_model(self, model_name: str) -> Optional[str]:
        """
        Get app ID for a given model name.

        Args:
            model_name: The model name from the request

        Returns:
            The corresponding app ID, or None if not found
        """
        config = self.get_app_config_for_model(model_name)
        return config.app_id if config else None

    def get_app_config_for_model(self, model_name: str) -> Optional[AppConfig]:
        """
        Get full app configuration for a given model name.

        Args:
            model_name: The model name from the request

        Returns:
            The corresponding AppConfig, or None if not found
        """
        mapping = self.get_app_config_mapping()
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