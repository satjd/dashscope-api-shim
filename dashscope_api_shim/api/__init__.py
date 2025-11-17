"""API route handlers for the DashScope shim."""

from dashscope_api_shim.api.chat import router as chat_router
from dashscope_api_shim.api.models import router as models_router

__all__ = ["chat_router", "models_router"]