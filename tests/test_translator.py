"""Tests for the DashScope translator."""

import pytest
from dashscope_api_shim.core.translator import DashScopeTranslator
from dashscope_api_shim.models.openai import ChatCompletionRequest, ChatMessage


@pytest.fixture
def translator():
    """Create a translator instance."""
    return DashScopeTranslator()


@pytest.fixture
def sample_openai_request():
    """Create a sample OpenAI request."""
    return ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello, how are you?"),
        ],
        temperature=0.7,
        max_tokens=150,
    )


def test_translate_model_name(translator):
    """Test model name translation."""
    # Test with mapping
    assert translator.translate_model_name("gpt-3.5-turbo") == "qwen-turbo"
    assert translator.translate_model_name("gpt-4") == "qwen-plus"

    # Test without mapping (pass-through)
    assert translator.translate_model_name("qwen-max") == "qwen-max"
    assert translator.translate_model_name("custom-model") == "custom-model"


def test_openai_to_dashscope(translator, sample_openai_request):
    """Test OpenAI to DashScope request conversion."""
    dashscope_request = translator.openai_to_dashscope(sample_openai_request)

    # Check model translation
    assert dashscope_request.model == "qwen-turbo"

    # Check messages
    assert len(dashscope_request.input.messages) == 2
    assert dashscope_request.input.messages[0].role == "system"
    assert dashscope_request.input.messages[0].content == "You are a helpful assistant."
    assert dashscope_request.input.messages[1].role == "user"
    assert dashscope_request.input.messages[1].content == "Hello, how are you?"

    # Check parameters
    assert dashscope_request.parameters.temperature == 0.7
    assert dashscope_request.parameters.max_tokens == 150


def test_dashscope_to_openai(translator, sample_openai_request):
    """Test DashScope to OpenAI response conversion."""
    dashscope_response = {
        "request_id": "test-request-id",
        "output": {
            "text": "I'm doing well, thank you for asking!",
            "finish_reason": "stop",
        },
        "usage": {
            "input_tokens": 20,
            "output_tokens": 10,
            "total_tokens": 30,
        },
    }

    openai_response = translator.dashscope_to_openai(
        dashscope_response, sample_openai_request
    )

    # Check response structure
    assert openai_response.object == "chat.completion"
    assert openai_response.model == "gpt-3.5-turbo"
    assert len(openai_response.choices) == 1

    # Check choice
    choice = openai_response.choices[0]
    assert choice.index == 0
    assert choice.message.role == "assistant"
    assert choice.message.content == "I'm doing well, thank you for asking!"
    assert choice.finish_reason == "stop"

    # Check usage
    assert openai_response.usage.prompt_tokens == 20
    assert openai_response.usage.completion_tokens == 10
    assert openai_response.usage.total_tokens == 30


@pytest.mark.asyncio
async def test_create_chat_completion_mock(translator, sample_openai_request, mocker):
    """Test create_chat_completion with mocked HTTP client."""
    # Mock the httpx client
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "request_id": "test-request-id",
        "output": {
            "text": "Mocked response",
            "finish_reason": "stop",
        },
        "usage": {
            "input_tokens": 15,
            "output_tokens": 5,
            "total_tokens": 20,
        },
    }
    mock_response.raise_for_status = mocker.Mock()

    mock_client = mocker.AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    # Call the method
    response = await translator.create_chat_completion(
        sample_openai_request, "test-api-key"
    )

    # Verify response
    assert response.choices[0].message.content == "Mocked response"
    assert response.usage.total_tokens == 20