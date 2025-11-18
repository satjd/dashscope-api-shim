# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based API shim that provides OpenAI Chat Completions API compatibility for Aliyun Bailian applications. It allows OpenAI-compatible clients to seamlessly use Bailian apps with advanced chain-of-thought reasoning support, similar to OpenAI's o1 model.

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
make docker-run          # Run container (requires DASHSCOPE_API_KEY and BAILIAN_APP_ID)
make docker-stop         # Stop and remove container
make docker-logs         # View container logs
```

## Architecture

### Core Request Flow

The application follows this request flow:

1. **API Layer** (`dashscope_api_shim/api/chat.py`): FastAPI endpoint receives OpenAI-formatted request
2. **Reasoning Parameter Extraction** (`dashscope_api_shim/core/bailian_translator.py`): Extracts `reasoning_effort` and thinking parameters
3. **Message Conversion**: Converts OpenAI messages array to Bailian prompt format
4. **Bailian API Call**: Makes request to Bailian App API with thinking parameters
5. **Response Processing**: Extracts answer and optional reasoning content
6. **OpenAI Format Response**: Returns OpenAI-compatible ChatCompletionResponse or SSE stream

### Key Components

**BailianTranslator** (`core/bailian_translator.py`): The core translation engine
- `messages_to_prompt()`: Converts OpenAI messages array to a single prompt string
- `extract_answer_text()`: Extracts answer text from Bailian API response
- `extract_reasoning_delta()`: Extracts reasoning/thinking content for streaming
- `sanitize_reasoning()`: Truncates and cleans reasoning text to max length
- `_get_thinking_params()`: Extracts thinking parameters from request (has_thoughts, enable_thinking, incremental_output)
- `create_chat_completion()`: Handles non-streaming requests
- `create_chat_completion_stream()`: Handles SSE streaming requests with reasoning support

**Pydantic Models** (`models/`):
- `models/openai.py`: OpenAI API data models with reasoning_effort extension
  - `ChatCompletionRequest`: Includes `reasoning_effort` field ('low', 'medium', 'high')
  - `ChatCompletionResponse`: Standard OpenAI response format
  - `ChatCompletionChunk`: For streaming responses
  - `ChoiceDelta`: For streaming deltas with reasoning_content support

**Configuration** (`core/config.py`):
- Uses pydantic-settings for environment-based configuration
- Settings loaded from `.env` file
- Required: `DASHSCOPE_API_KEY`, `BAILIAN_APP_ID`
- Optional: `DASHSCOPE_BASE_URL`, `BAILIAN_REASONING_DELTA_MAX`, `REQUEST_TIMEOUT`

**API Routers**:
- `api/chat.py`: `/v1/chat/completions` endpoint (supports both streaming and non-streaming)
- `api/models.py`: `/v1/models` endpoint (returns Bailian app model)

### Authentication

API key authentication is handled via the `Authorization: Bearer <token>` header. The token is extracted by `get_api_key()` dependency in `api/chat.py` and passed to Bailian API. Falls back to `DASHSCOPE_API_KEY` environment variable if header is not provided.

### Reasoning Support

The application supports OpenAI o1-style reasoning via the `reasoning_effort` parameter:

| reasoning_effort | has_thoughts | enable_thinking | Behavior |
|-----------------|--------------|-----------------|----------|
| 'low' (default) | False | True | Thinking enabled, reasoning hidden |
| 'medium' | True | True | Thinking enabled, reasoning visible |
| 'high' | True | True | Thinking enabled, reasoning visible |

**Implementation Details:**
- `reasoning_effort='low'`: Bailian thinks internally but reasoning content is not sent to client
- `reasoning_effort='medium'` or `'high'`: Reasoning chunks are streamed via `reasoning_content` field in deltas
- Initial reasoning indicator ("正在思考...") only sent when `has_thoughts=True`
- Reasoning content extracted from Bailian's `thoughts` array and sanitized to max length

### Streaming vs Non-Streaming

- **Non-streaming**: Returns complete `ChatCompletionResponse` with answer text
- **Streaming**: Returns `StreamingResponse` with SSE (Server-Sent Events) format
  - Role chunk: `{"delta": {"role": "assistant"}}`
  - Reasoning chunk (if has_thoughts): `{"delta": {"reasoning_content": "..."}}`
  - Content chunks: `{"delta": {"content": "..."}}`
  - Final chunk: `{"delta": {}, "finish_reason": "stop"}`
- Streaming detection: Based on `request.stream` boolean in ChatCompletionRequest
- Bailian streaming uses `incremental_output=True` parameter

## Configuration

The application uses pydantic-settings with `.env` file.

### Required Variables
- `DASHSCOPE_API_KEY`: Your DashScope API key
- `BAILIAN_APP_ID`: Your Bailian application ID

### Optional Variables
- `DASHSCOPE_BASE_URL`: DashScope API endpoint (default: `https://dashscope.aliyuncs.com/api/v1`)
- `BAILIAN_REASONING_DELTA_MAX`: Maximum reasoning content length per chunk (default: 180 characters)
- `REQUEST_TIMEOUT`: API request timeout in seconds (default: 600 seconds for long reasoning tasks)

See `.env.example` for all available configuration options.

## Code Style

- Line length: 100 characters (black and ruff)
- Type hints required: mypy strict mode (`disallow_untyped_defs = true`)
- Import ordering: isort via ruff
- Pre-commit hooks enforce: black, ruff, mypy, trailing whitespace, JSON/YAML/TOML validation
