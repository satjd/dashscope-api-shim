"""Translator for Bailian App (百炼) integration."""

import json
import re
import time
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from dashscope_api_shim.core.config import settings
from dashscope_api_shim.models.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    Usage,
)
from dashscope_api_shim.utils.logger import get_logger

logger = get_logger(__name__)


class BailianTranslator:
    """Translator for Bailian App integration with reasoning support."""

    def __init__(self):
        """Initialize the Bailian translator."""
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.app_id = settings.BAILIAN_APP_ID
        self.reasoning_max_len = settings.BAILIAN_REASONING_DELTA_MAX
        self.timeout = settings.REQUEST_TIMEOUT

        if not self.app_id:
            raise ValueError("BAILIAN_APP_ID is required. Please set it in your .env file.")

    def messages_to_prompt(self, messages: List[ChatMessage]) -> str:
        """
        Convert OpenAI messages format to a single prompt string.

        Args:
            messages: List of chat messages

        Returns:
            Formatted prompt string
        """
        parts = []
        for message in messages:
            role = message.role
            content = message.content

            # Handle content that might be a list of parts
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_parts.append(part['text'])
                    elif isinstance(part, dict) and 'type' in part and part['type'] == 'text':
                        text_parts.append(part.get('text', ''))
                text = ''.join(text_parts)
            else:
                text = str(content) if content else ''

            parts.append(f"{role}: {text}")

        return "\n".join(parts)

    def extract_answer_text(self, response_obj: Dict[str, Any]) -> str:
        """
        Extract the answer text from Bailian response.

        Args:
            response_obj: Bailian API response object

        Returns:
            Extracted answer text
        """
        if not isinstance(response_obj, dict):
            return ""

        # Try multiple possible paths for the answer
        output = response_obj.get('output', {})
        return (
            output.get('text', '') or
            response_obj.get('text', '') or
            response_obj.get('output_text', '') or
            ""
        )

    def extract_reasoning_delta(self, response_obj: Dict[str, Any]) -> str:
        """
        Extract reasoning/thinking content from Bailian response.

        Args:
            response_obj: Bailian API response object

        Returns:
            Reasoning text delta
        """
        if not isinstance(response_obj, dict):
            return ""

        output = response_obj.get('output', {})
        thoughts = output.get('thoughts', [])

        reasoning_pieces = []
        for thought in thoughts:
            if not isinstance(thought, dict):
                continue

            # Look for reasoning type thoughts
            if thought.get('action_type') == 'reasoning':
                thought_content = thought.get('thought')
                if thought_content is None:
                    continue

                if isinstance(thought_content, str):
                    reasoning_pieces.append(thought_content)
                elif isinstance(thought_content, dict):
                    text = thought_content.get('text') or thought_content.get('content', '')
                    reasoning_pieces.append(text)
                else:
                    reasoning_pieces.append(str(thought_content))

        return "".join(reasoning_pieces)

    def _get_thinking_params(self, request: ChatCompletionRequest) -> tuple[bool, bool, bool]:
        """
        Extract thinking parameters from request.

        Args:
            request: Chat completion request

        Returns:
            Tuple of (has_thoughts, enable_thinking, incremental_output)
        """
        extra_params = request.model_dump(exclude_unset=True)

        # Map reasoning_effort to enable_thinking (OpenAI o1-style)
        reasoning_effort = request.reasoning_effort or extra_params.get("reasoning_effort")
        if reasoning_effort:
            effort_lower = reasoning_effort.lower()
            if effort_lower == "low":
                # Low: Enable thinking but disable thoughts display
                enable_thinking = True
                has_thoughts = False
            else:  # medium or high
                # Medium/High: Enable both thinking and thoughts display
                enable_thinking = True
                has_thoughts = True
        else:
            # Fall back to legacy parameters (disabled by default)
            has_thoughts = extra_params.get("has_thoughts", False)
            enable_thinking = extra_params.get("enable_thinking", False)

        incremental_output = extra_params.get("incremental_output", True)

        return has_thoughts, enable_thinking, incremental_output

    def sanitize_reasoning(self, text: str) -> str:
        """
        Sanitize and truncate reasoning text to avoid exposing full chain-of-thought.

        Args:
            text: Raw reasoning text

        Returns:
            Sanitized reasoning text
        """
        if not text:
            return ""

        # Remove code blocks
        text = re.sub(r"```.*?```", "", text, flags=re.S)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove step indicators
        text = re.sub(r"(Step\s*\d+[:）\-]?)", "", text, flags=re.I)
        text = re.sub(r"(^|\s)\d+[\.\)]\s*", " ", text)

        # Truncate if too long
        if len(text) > self.reasoning_max_len:
            text = text[:self.reasoning_max_len].rstrip() + "..."

        return text

    async def create_chat_completion(
        self,
        request: ChatCompletionRequest,
        api_key: str
    ) -> ChatCompletionResponse:
        """
        Create a non-streaming chat completion using Bailian App.

        Args:
            request: OpenAI-style chat completion request
            api_key: DashScope API key

        Returns:
            OpenAI-style chat completion response
        """

        # Convert messages to prompt
        prompt = self.messages_to_prompt(request.messages)

        # Get thinking parameters
        has_thoughts, enable_thinking, incremental_output = self._get_thinking_params(request)

        # Build Bailian request
        url = f"{self.base_url}/apps/{self.app_id}/completion"
        payload = {
            "input": {"prompt": prompt},
            "parameters": {
                "incremental_output": incremental_output,
                "has_thoughts": has_thoughts,
                "enable_thinking": enable_thinking
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)

            if not response.is_success:
                error_data = response.json() if response.content else {"error": response.text}
                logger.error(f"Bailian API error: {error_data}")
                raise httpx.HTTPStatusError(
                    f"Bailian API error: {error_data}",
                    request=response.request,
                    response=response
                )

            data = response.json()
            answer = self.extract_answer_text(data)

            # Create OpenAI-style response
            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                object="chat.completion",
                created=int(time.time()),
                model=f"bailian-app-{self.app_id}",
                choices=[
                    Choice(
                        index=0,
                        message=ChatMessage(role="assistant", content=answer),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=len(prompt.split()),
                    completion_tokens=len(answer.split()),
                    total_tokens=len(prompt.split()) + len(answer.split())
                )
            )

    async def create_chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        api_key: str
    ) -> AsyncGenerator[str, None]:
        """
        Create a streaming chat completion using Bailian App with reasoning support.

        Args:
            request: OpenAI-style chat completion request
            api_key: DashScope API key

        Yields:
            SSE-formatted response chunks
        """

        # Convert messages to prompt
        prompt = self.messages_to_prompt(request.messages)

        # Get thinking parameters
        has_thoughts, enable_thinking, incremental_output = self._get_thinking_params(request)

        # Build Bailian request
        url = f"{self.base_url}/apps/{self.app_id}/completion"
        payload = {
            "input": {"prompt": prompt},
            "parameters": {
                "incremental_output": incremental_output,
                "has_thoughts": has_thoughts,
                "enable_thinking": enable_thinking
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "text/event-stream",
            "X-DashScope-SSE": "enable"
        }

        chat_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        model_name = f"bailian-app-{self.app_id}"
        created_time = int(time.time())

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if not response.is_success:
                    error_text = await response.aread()
                    logger.error(f"Bailian API stream error: {error_text}")
                    error_chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": model_name,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": f"Error: {error_text.decode('utf-8', errors='ignore')}"
                            },
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                # Send initial role chunk
                role_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant"},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(role_chunk, ensure_ascii=False)}\n\n"

                # Send initial reasoning indicator only if has_thoughts is enabled
                if has_thoughts:
                    reasoning_start = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": model_name,
                        "choices": [{
                            "index": 0,
                            "delta": {"reasoning_content": "正在思考..."},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(reasoning_start, ensure_ascii=False)}\n\n"

                buffer = ""
                prev_answer_full = ""
                prev_reasoning_full = ""

                async for chunk in response.aiter_text():
                    buffer += chunk

                    # Process complete SSE events
                    while "\n\n" in buffer:
                        event_data, buffer = buffer.split("\n\n", 1)

                        # Extract data from SSE event
                        data_lines = []
                        for line in event_data.splitlines():
                            if line.startswith("data:"):
                                data_lines.append(line[5:].lstrip())

                        if not data_lines:
                            continue

                        data_str = "\n".join(data_lines).strip()

                        if data_str == "[DONE]":
                            # Send completion chunk
                            done_chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created_time,
                                "model": model_name,
                                "choices": [{
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": "stop"
                                }]
                            }
                            yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
                            yield "data: [DONE]\n\n"
                            return

                        try:
                            obj = json.loads(data_str)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse SSE data: {e}")
                            continue

                        # Extract and process reasoning content only if has_thoughts is enabled
                        if has_thoughts:
                            reasoning_full = self.extract_reasoning_delta(obj)
                            if reasoning_full:
                                # Calculate delta
                                reasoning_delta = reasoning_full
                                if reasoning_full.startswith(prev_reasoning_full):
                                    reasoning_delta = reasoning_full[len(prev_reasoning_full):]
                                prev_reasoning_full = reasoning_full

                                # Sanitize and send reasoning chunk
                                safe_reasoning = self.sanitize_reasoning(reasoning_delta)
                                if safe_reasoning:
                                    reasoning_chunk = {
                                        "id": chat_id,
                                        "object": "chat.completion.chunk",
                                        "created": created_time,
                                        "model": model_name,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {"reasoning_content": safe_reasoning},
                                            "finish_reason": None
                                        }]
                                    }
                                    yield f"data: {json.dumps(reasoning_chunk, ensure_ascii=False)}\n\n"

                        # Extract and process answer content
                        answer_full = self.extract_answer_text(obj)
                        if answer_full:
                            # Calculate delta
                            answer_delta = answer_full
                            if answer_full.startswith(prev_answer_full):
                                answer_delta = answer_full[len(prev_answer_full):]
                            prev_answer_full = answer_full

                            if answer_delta:
                                content_chunk = {
                                    "id": chat_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": model_name,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"content": answer_delta},
                                        "finish_reason": None
                                    }]
                                }
                                yield f"data: {json.dumps(content_chunk, ensure_ascii=False)}\n\n"

                        # Check for completion
                        if obj.get("finish_reason") == "stop" or obj.get("is_end") is True:
                            done_chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created_time,
                                "model": model_name,
                                "choices": [{
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": "stop"
                                }]
                            }
                            yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
                            yield "data: [DONE]\n\n"
                            return