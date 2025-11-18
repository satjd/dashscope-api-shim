"""Main FastAPI application for DashScope API Shim."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dashscope_api_shim import __version__
from dashscope_api_shim.api import chat_router, models_router
from dashscope_api_shim.core.config import settings
from dashscope_api_shim.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info(f"Starting DashScope API Shim v{__version__}")
    logger.info(f"Server running on {settings.HOST}:{settings.PORT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")

    yield

    # Shutdown
    logger.info("Shutting down DashScope API Shim")


# Create FastAPI application
app = FastAPI(
    title="Bailian App API Shim",
    description="OpenAI-compatible API for Aliyun Bailian (百炼) applications with reasoning support",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Include routers
app.include_router(chat_router, prefix="/v1", tags=["Chat"])
app.include_router(models_router, prefix="/v1", tags=["Models"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "name": "Bailian App API Shim",
        "version": __version__,
        "description": "OpenAI-compatible API for Aliyun Bailian applications",
        "documentation": "/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": __version__}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "An internal server error occurred",
                "type": "internal_server_error",
                "code": 500,
            }
        },
    )


def main():
    """Run the application using uvicorn."""
    import uvicorn

    uvicorn.run(
        "dashscope_api_shim.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()