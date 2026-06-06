"""OpenAI chat completions provider."""
from __future__ import annotations

import os
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment]

from guardian_runtime.providers.base import ProviderResult


class OpenAIProvider:
    """Wraps OpenAI chat.completions.create."""

    name = "openai"

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            if OpenAI is None:
                raise ImportError(
                    "OpenAI SDK not installed. Run: pip install guardian-runtime[openai]"
                )
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY is not set. Export your key or use provider='gemini'."
                )
            self._client = OpenAI(api_key=api_key)
        return self._client

    def complete(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ProviderResult:
        client = self._get_client()
        reserved = {"provider", "raise_on_block"}
        llm_kwargs = {k: v for k, v in kwargs.items() if k not in reserved}
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            **llm_kwargs,
        )
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        return ProviderResult(
            content=content,
            raw_response=completion,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
        )

    def stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        client = self._get_client()
        reserved = {"provider", "raise_on_block"}
        llm_kwargs = {k: v for k, v in kwargs.items() if k not in reserved}
        llm_kwargs.pop("stream_options", None)
        
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            **llm_kwargs,
        )
        
        content = ""
        usage = None
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                content += text
                yield text
            if getattr(chunk, "usage", None):
                usage = chunk.usage
                
        return ProviderResult(
            content=content,
            raw_response=None,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
        )
