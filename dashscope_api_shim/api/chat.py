"""Chat completions API endpoint."""

from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse

from dashscope_api_shim.core.bailian_translator import BailianTranslator
from dashscope_api_shim.core.config import settings
from dashscope_api_shim.models.openai import ChatCompletionRequest, ChatCompletionResponse
from dashscope_api_shim.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
translator = BailianTranslator()


async def get_api_key(authorization: Optional[str] = Header(None)) -> str:
    """Extract API key from Authorization header."""
    # Allow fallback to env var if authorization not provided
    if not authorization:
        if settings.DASHSCOPE_API_KEY:
            return settings.DASHSCOPE_API_KEY
        raise HTTPException(status_code=401, detail="Authorization header required")

    if authorization.startswith("Bearer "):
        return authorization[7:]

    raise HTTPException(status_code=401, detail="Invalid authorization format")


@router.post("/chat/completions", response_model=None)
async def create_chat_completion(
    request: ChatCompletionRequest,
    api_key: str = Depends(get_api_key),
) -> Union[ChatCompletionResponse, StreamingResponse]:
    """
    Create a chat completion using Bailian App.

    This endpoint uses Bailian App API with reasoning support for all requests.
    Maps the requested model name to the corresponding Bailian app ID.
    """
    try:
        logger.info(f"Processing chat completion request for model: {request.model}")

        # Get app config for the requested model
        app_config = settings.get_app_config_for_model(request.model)
        if not app_config:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "message": f"Model '{request.model}' not found. Please check /v1/models for available models.",
                        "type": "invalid_request_error",
                        "code": "model_not_found",
                    }
                },
            )

        logger.info(f"Using Bailian app ID: {app_config.app_id} (enable_thinking={app_config.enable_thinking}, has_thoughts={app_config.has_thoughts})")

        # Use Bailian translator with the mapped app_config
        if request.stream:
            stream = translator.create_chat_completion_stream(request, api_key, app_config)
            return StreamingResponse(
                stream,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            response = await translator.create_chat_completion(request, api_key, app_config)
            return response

    except Exception as e:
        logger.error(f"Error processing chat completion: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "internal_error",
                    "code": "internal_error",
                }
            },
        )