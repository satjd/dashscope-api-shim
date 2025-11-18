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

    Returns a list of all configured Bailian app models from the mapping.
    """
    app_mapping = settings.get_app_mapping()
    created_time = int(time.time())

    models = [
        {
            "id": model_name,
            "object": "model",
            "created": created_time,
            "owned_by": "bailian",
            "permission": [],
            "root": model_name,
            "parent": None,
        }
        for model_name in app_mapping.keys()
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
    app_id = settings.get_app_id_for_model(model_id)

    if not app_id:
        available_models = list(settings.get_app_mapping().keys())
        return {
            "error": {
                "message": f"Model '{model_id}' not found. Available models: {', '.join(available_models)}",
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
        "description": f"Bailian application (app_id: {app_id}) with reasoning support",
    }