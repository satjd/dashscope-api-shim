"""Logging configuration for DashScope API Shim."""

import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or "dashscope_shim")

    # Only configure if not already configured
    if not logger.hasHandlers():
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Set level from environment or default
        from dashscope_api_shim.core.config import settings

        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    return logger