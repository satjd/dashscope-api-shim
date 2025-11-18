# Bailian App API Shim v0.1.0

🎉 **First stable release of Bailian App API Shim!**

This release provides a fully functional OpenAI-compatible API shim for Aliyun Bailian applications, with advanced reasoning support similar to OpenAI's o1 model.

## ✨ Features

### Core Functionality
- **OpenAI Chat Completions API Compatibility**: Drop-in replacement for OpenAI API clients
- **Bailian App Integration**: Seamless integration with Aliyun Bailian applications
- **Chain-of-Thought Reasoning**: Support for exposing AI reasoning process
- **OpenAI o1-style Parameters**: `reasoning_effort` parameter for controlling thinking depth
- **Server-Sent Events (SSE) Streaming**: Real-time streaming responses
- **FastAPI-based Implementation**: Modern async Python web framework
- **Docker Support**: Production-ready containerization

### API Endpoints
- `POST /v1/chat/completions` - Chat completion with optional reasoning
- `GET /v1/models` - List available Bailian app model
- `GET /health` - Health check endpoint

### Reasoning Modes
| reasoning_effort | Behavior |
|-----------------|----------|
| Not specified | Fast responses without reasoning (default) |
| `"low"` | Thinking enabled, reasoning hidden from output |
| `"medium"` | Thinking enabled, reasoning displayed |
| `"high"` | Thinking enabled, reasoning displayed |

## 📦 Installation

### Using pip
```bash
pip install dashscope-api-shim
```

### Using uv (recommended)
```bash
uv pip install dashscope-api-shim
```

### Using Docker
```bash
docker pull ghcr.io/satjd/dashscope-api-shim:v0.1.0
```

## 🚀 Quick Start

1. Set up environment variables:
```bash
export DASHSCOPE_API_KEY=your_api_key
export BAILIAN_APP_ID=your_app_id
```

2. Run the server:
```bash
uvicorn dashscope_api_shim.main:app --host 0.0.0.0 --port 8000
```

3. Use with any OpenAI-compatible client:
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your_dashscope_api_key"
)

# With reasoning effort control
response = client.chat.completions.create(
    model="bailian-app-your_app_id",
    messages=[{"role": "user", "content": "Solve this problem"}],
    extra_body={"reasoning_effort": "medium"}
)
```

## 🔧 Configuration

Required environment variables:
- `DASHSCOPE_API_KEY`: Your DashScope API key
- `BAILIAN_APP_ID`: Your Bailian application ID

Optional:
- `DASHSCOPE_BASE_URL`: API endpoint (default: https://dashscope.aliyuncs.com/api/v1)
- `BAILIAN_REASONING_DELTA_MAX`: Max reasoning length (default: 180)

## 📝 Changelog

### v0.1.0 (2024-11-18)
- Initial release
- Full OpenAI Chat Completions API compatibility
- Bailian App integration
- OpenAI o1-style reasoning support
- Streaming and non-streaming modes
- Docker support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Inspired by OpenAI's o1 model reasoning capabilities
- Powered by Aliyun Bailian platform

---

**Full Changelog**: https://github.com/satjd/dashscope-api-shim/commits/v0.1.0