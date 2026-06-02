"""OpenAI chat completions provider."""
from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from guardian.providers.base import ProviderResult


class OpenAIProvider:
    """Wraps OpenAI chat.completions.create."""

    name = "openai"

    def __init__(self, client: OpenAI | None = None) -> None:
        self._client = client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
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
        reserved = {"provider", "raise_on_block"}
        llm_kwargs = {k: v for k, v in kwargs.items() if k not in reserved}
        completion = self.client.chat.completions.create(
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
