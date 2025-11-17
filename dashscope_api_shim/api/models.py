"""Models API endpoint."""

from typing import List
import time

from fastapi import APIRouter

from dashscope_api_shim.core.config import settings
from dashscope_api_shim.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/models")
async def list_models():
    """
    List available Bailian app models.

    Returns a list of Bailian app models formatted as OpenAI model objects.
    """
    model_id = f"bailian-app-{settings.BAILIAN_APP_ID}"

    models = [
        {
            "id": model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "bailian",
            "permission": [],
            "root": model_id,
            "parent": None,
        }
    ]

    return {
        "object": "list",
        "data": models,
    }


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """
    Get a specific model.

    Args:
        model_id: The ID of the model to retrieve

    Returns:
        Model information in OpenAI format
    """
    bailian_model_id = f"bailian-app-{settings.BAILIAN_APP_ID}"

    # Only support the configured Bailian app model
    if model_id != bailian_model_id:
        return {
            "error": {
                "message": f"Model '{model_id}' not found. Only '{bailian_model_id}' is available.",
                "type": "invalid_request_error",
                "code": "model_not_found",
            }
        }

    return {
        "id": model_id,
        "object": "model",
        "created": int(time.time()),
        "owned_by": "bailian",
        "permission": [],
        "root": model_id,
        "parent": None,
        "description": "Bailian application with reasoning support",
    }