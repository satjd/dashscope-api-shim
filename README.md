# Bailian App API Shim

An OpenAI-compatible API shim for Aliyun Bailian (百炼) applications with advanced reasoning support and multi-app routing. Enables seamless integration of Bailian apps with OpenAI-compatible clients like Cherry Studio, Continue, and more.

## Features

- **OpenAI Chat Completions API Compatible** - Works with any OpenAI-compatible client
- **Bailian App Integration** - Direct integration with Aliyun Bailian applications
- **Multi-App Routing** (v0.2.0+) - Map multiple Bailian apps to different model names
- **Reasoning Support** - Built-in support for chain-of-thought reasoning (similar to OpenAI o1)
- **Streaming with SSE** - Server-Sent Events streaming for real-time responses
- **Reasoning Effort Control** - OpenAI o1-style `reasoning_effort` parameter
- **FastAPI-based** - High-performance async request handling
- **Type-safe** - Full Pydantic model validation
- **Easy Deployment** - Docker support included

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/satjd/dashscope-api-shim.git
cd dashscope-api-shim

# Create a virtual environment using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

### Single App Mode (Legacy)

```env
# DashScope/Bailian Configuration (Required)
DASHSCOPE_API_KEY=sk-your_dashscope_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# Bailian App Configuration (Single App)
BAILIAN_APP_ID=your_bailian_app_id
BAILIAN_REASONING_DELTA_MAX=180

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### Multi-App Mode (v0.2.0+)

```env
# DashScope/Bailian Configuration (Required)
DASHSCOPE_API_KEY=sk-your_dashscope_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# Bailian App Configuration (Multiple Apps)
# Simple format: Map model names to Bailian app IDs
BAILIAN_APP_MAPPING='{"bailian-app-reasoning":"app_id_1","bailian-app-fast":"app_id_2"}'

# Extended format: Map with per-app default thinking parameters
# BAILIAN_APP_MAPPING='{"bailian-app-reasoning":{"app_id":"app_id_1","enable_thinking":true,"has_thoughts":false},"bailian-app-fast":{"app_id":"app_id_2","enable_thinking":false}}'

BAILIAN_REASONING_DELTA_MAX=180

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

**Per-App Default Thinking Parameters** (v0.2.0+):
The extended format allows you to configure default `enable_thinking` and `has_thoughts` for each app:
- `enable_thinking`: Whether to enable internal thinking (improves quality but slower)
- `has_thoughts`: Whether to show reasoning process to users

These defaults can be overridden per-request using `reasoning_effort` or explicit parameters.

See `.env.example` for all available configuration options.

## Usage

### Running the Server

```bash
# Using uvicorn directly
uvicorn dashscope_api_shim.main:app --host 0.0.0.0 --port 8000 --reload

# Or use the main module
python -m dashscope_api_shim.main
```

### API Endpoints

The shim provides OpenAI-compatible endpoints:

- `POST /v1/chat/completions` - Chat completions endpoint
- `GET /v1/models` - List available models
- `GET /health` - Health check endpoint

### Example Request

```python
import openai

# Configure OpenAI client to use the shim
client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your_dashscope_api_key"
)

# Single-app mode (legacy) - auto-generated model name
response = client.chat.completions.create(
    model="bailian-app-your_app_id",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

# Multi-app mode (v0.2.0+) - use custom model names from BAILIAN_APP_MAPPING
response = client.chat.completions.create(
    model="bailian-app-reasoning",  # Maps to specific app_id via config
    messages=[
        {"role": "user", "content": "Solve this complex problem..."}
    ]
)

print(response.choices[0].message.content)

# With reasoning (OpenAI o1-style) using another configured app
response = client.chat.completions.create(
    model="bailian-app-fast",  # Another app from BAILIAN_APP_MAPPING
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ],
    reasoning_effort="medium",  # or "low", "high"
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Using with curl

```bash
# Single-app mode (legacy)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_dashscope_api_key" \
  -d '{
    "model": "bailian-app-your_app_id",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Multi-app mode (v0.2.0+) with custom model names
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_dashscope_api_key" \
  -d '{
    "model": "bailian-app-reasoning",
    "messages": [{"role": "user", "content": "Explain recursion"}],
    "stream": true,
    "reasoning_effort": "high"
  }'

# List available models
curl -X GET http://localhost:8000/v1/models \
  -H "Authorization: Bearer your_dashscope_api_key"
```

## Reasoning Support

This shim supports OpenAI o1-style reasoning with the `reasoning_effort` parameter:

| Parameter Value | Behavior |
|----------------|----------|
| Not specified | No thinking (fast, default) |
| `"low"` | Thinking enabled, reasoning hidden |
| `"medium"` | Thinking enabled, reasoning visible |
| `"high"` | Thinking enabled, reasoning visible |

### Legacy Parameters

You can also use the legacy parameters for fine-grained control:

```json
{
  "has_thoughts": true,
  "enable_thinking": true,
  "incremental_output": true
}
```

## Development

### Project Structure

```
dashscope-api-shim/
├── dashscope_api_shim/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── api/
│   │   ├── chat.py              # Chat completions endpoint
│   │   └── models.py            # Models endpoint
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   └── bailian_translator.py # Bailian app translator
│   ├── models/
│   │   └── openai.py            # OpenAI-compatible models
│   └── utils/
│       └── logger.py            # Logging
├── .env.example                 # Environment template
├── requirements.txt             # Dependencies
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dashscope_api_shim --cov-report=html

# Run specific test file
pytest tests/test_translator.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black dashscope_api_shim tests

# Run linter
ruff check dashscope_api_shim tests

# Type checking
mypy dashscope_api_shim

# Run all checks
pre-commit run --all-files
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pre-commit install
```

## Docker

### Building the Image

```bash
docker build -t dashscope-api-shim .
```

### Running with Docker

```bash
docker run -d \
  -p 8000:8000 \
  -e DASHSCOPE_API_KEY=your_api_key \
  --name dashscope-api-shim \
  dashscope-api-shim
```

### Docker Compose

```yaml
version: '3.8'

services:
  dashscope-api-shim:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

## Supported Models

This shim supports Bailian (百炼) applications:

### Single App Mode (Legacy)
- Configure one app via `BAILIAN_APP_ID`
- Auto-generated model name: `bailian-app-{your_app_id}`

### Multi-App Mode (v0.2.0+)
- Configure multiple apps via `BAILIAN_APP_MAPPING`
- Custom model names mapping to different app IDs
- Example: `{"bailian-app-reasoning": "app_id_1", "bailian-app-fast": "app_id_2"}`
- Each model can have different capabilities based on the Bailian app configuration

All models support:
- Full reasoning and chain-of-thought support
- OpenAI o1-style `reasoning_effort` parameter
- Streaming with Server-Sent Events (SSE)
- Standard OpenAI Chat Completions API format

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Inspired by OpenAI's API design (especially o1 reasoning)
- Powered by Aliyun Bailian (百炼)

## Support

For issues, questions, or suggestions, please open an issue on GitHub.