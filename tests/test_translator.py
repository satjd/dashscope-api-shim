"""Tests for the Bailian translator."""

import pytest
from dashscope_api_shim.core.bailian_translator import BailianTranslator
from dashscope_api_shim.models.openai import ChatCompletionRequest, ChatMessage


@pytest.fixture
def translator():
    """Create a translator instance."""
    return BailianTranslator()


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


def test_messages_to_prompt(translator):
    """Test messages to prompt conversion."""
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="Hello!"),
        ChatMessage(role="assistant", content="Hi there!"),
        ChatMessage(role="user", content="How are you?"),
    ]

    prompt = translator.messages_to_prompt(messages)

    # Check prompt format
    assert "You are a helpful assistant." in prompt
    assert "Hello!" in prompt
    assert "Hi there!" in prompt
    assert "How are you?" in prompt


def test_extract_answer_text(translator):
    """Test extracting answer text from Bailian response."""
    # Test with text in output
    response1 = {
        "output": {
            "text": "Hello, world!"
        }
    }
    assert translator.extract_answer_text(response1) == "Hello, world!"

    # Test with text at root level
    response2 = {
        "text": "Root level text"
    }
    assert translator.extract_answer_text(response2) == "Root level text"

    # Test with output_text
    response3 = {
        "output_text": "Output text field"
    }
    assert translator.extract_answer_text(response3) == "Output text field"

    # Test with no text
    response4 = {"output": {}}
    assert translator.extract_answer_text(response4) == ""


def test_get_thinking_params(translator):
    """Test thinking parameter extraction."""
    # Test default (reasoning_effort='low' by default)
    request1 = ChatCompletionRequest(
        model="test-model",
        messages=[ChatMessage(role="user", content="Hello")]
    )
    has_thoughts, enable_thinking, incremental = translator._get_thinking_params(request1)
    assert has_thoughts is False  # Low means thinking enabled but hidden
    assert enable_thinking is True
    assert incremental is True

    # Test explicit reasoning_effort='low'
    request2 = ChatCompletionRequest(
        model="test-model",
        messages=[ChatMessage(role="user", content="Hello")],
        reasoning_effort="low"
    )
    has_thoughts, enable_thinking, incremental = translator._get_thinking_params(request2)
    assert has_thoughts is False
    assert enable_thinking is True
    assert incremental is True

    # Test reasoning_effort='medium'
    request3 = ChatCompletionRequest(
        model="test-model",
        messages=[ChatMessage(role="user", content="Hello")],
        reasoning_effort="medium"
    )
    has_thoughts, enable_thinking, incremental = translator._get_thinking_params(request3)
    assert has_thoughts is True
    assert enable_thinking is True
    assert incremental is True

    # Test reasoning_effort='high'
    request4 = ChatCompletionRequest(
        model="test-model",
        messages=[ChatMessage(role="user", content="Hello")],
        reasoning_effort="high"
    )
    has_thoughts, enable_thinking, incremental = translator._get_thinking_params(request4)
    assert has_thoughts is True
    assert enable_thinking is True
    assert incremental is True