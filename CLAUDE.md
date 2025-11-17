# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based API shim that translates Aliyun DashScope API requests to OpenAI Chat Completions API format. It allows OpenAI-compatible clients to seamlessly use DashScope's language models (Qwen series).

## Development Commands

### Environment Setup
```bash
make install-dev          # Install dev dependencies and pre-commit hooks
make setup-env           # Create .env from .env.example
```

### Running the Server
```bash
make run                 # Run development server (http://0.0.0.0:8000)
uvicorn dashscope_api_shim.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
make test                # Run all tests
make test-cov            # Run tests with coverage report
pytest tests/test_translator.py  # Run specific test file
pytest -v                # Run with verbose output
```

### Code Quality
```bash
make format              # Format with black and ruff
make lint                # Run ruff and mypy
pre-commit run --all-files  # Run all pre-commit hooks
```

### Docker
```bash
make docker-build        # Build Docker image
make docker-run          # Run container (requires DASHSCOPE_API_KEY env var)
make docker-stop         # Stop and remove container
make docker-logs         # View container logs
```

## Architecture

### Core Translation Flow

The application follows this request flow:

1. **API Layer** (`dashscope_api_shim/api/chat.py`): FastAPI endpoint receives OpenAI-formatted request
2. **Translation** (`dashscope_api_shim/core/translator.py`): DashScopeTranslator converts between formats
3. **External API Call**: Makes request to DashScope API
4. **Response Translation**: Converts DashScope response back to OpenAI format
5. **Return**: Returns OpenAI-compatible response to client

### Key Components

**DashScopeTranslator** (`core/translator.py`): The core translation engine
- `openai_to_dashscope()`: Converts OpenAI ChatCompletionRequest to DashScope format
- `dashscope_to_openai()`: Converts DashScope response to OpenAI ChatCompletionResponse
- `translate_model_name()`: Maps OpenAI model names (e.g., gpt-3.5-turbo) to DashScope models (e.g., qwen-turbo)
- `create_chat_completion()`: Handles non-streaming requests
- `create_chat_completion_stream()`: Handles SSE streaming requests

**Pydantic Models** (`models/`):
- `models/openai.py`: OpenAI API data models (ChatCompletionRequest, ChatCompletionResponse, etc.)
- `models/dashscope.py`: DashScope API data models (DashScopeRequest, DashScopeMessage, etc.)

**Configuration** (`core/config.py`):
- Uses pydantic-settings for environment-based configuration
- Settings loaded from `.env` file
- Key config: `MODEL_MAPPING` dict maps OpenAI model names to DashScope equivalents

**API Routers**:
- `api/chat.py`: `/v1/chat/completions` endpoint (supports both streaming and non-streaming)
- `api/models.py`: `/v1/models` endpoint for model listing

### Authentication

API key authentication is handled via the `Authorization: Bearer <token>` header. The token is extracted by `get_api_key()` dependency in `api/chat.py` and passed to DashScope API.

### Streaming vs Non-Streaming

- Non-streaming: Returns complete `ChatCompletionResponse`
- Streaming: Returns `StreamingResponse` with SSE (Server-Sent Events) format
- Streaming detection: Based on `request.stream` boolean in ChatCompletionRequest
- DashScope streaming uses `incremental_output=True` parameter

## Configuration

The application uses pydantic-settings with `.env` file. Required variables:
- `DASHSCOPE_API_KEY`: Your DashScope API key (required)
- `DASHSCOPE_BASE_URL`: DashScope API endpoint (default: https://dashscope.aliyuncs.com/api/v1)

See `.env.example` for all available configuration options.

## Code Style

- Line length: 100 characters (black and ruff)
- Type hints required: mypy strict mode (`disallow_untyped_defs = true`)
- Import ordering: isort via ruff
- Pre-commit hooks enforce: black, ruff, mypy, trailing whitespace, JSON/YAML/TOML validation
