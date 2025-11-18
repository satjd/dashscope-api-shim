"""DashScope API Shim - Translate DashScope API to OpenAI Chat Completions API."""

__version__ = "0.2.0"
__author__ = "Ao Song"
__email__ = "songao60@foxmail.com"

from dashscope_api_shim.core.config import settings

__all__ = ["settings", "__version__"]