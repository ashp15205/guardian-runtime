"""Anthropic Claude provider."""
from __future__ import annotations

import os
from typing import Any

from guardian_runtime.providers.base import ProviderResult

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore[misc, assignment]


class AnthropicProvider:
    """Wraps Anthropic messages.create for Claude models."""

    name = "anthropic"

    def __init__(self, client: Any | None = None, api_key: str | None = None) -> None:
        self._client = client
        self._api_key = api_key

    @property
    def client(self) -> Any:
        if self._client is not None:
            return self._client
        if Anthropic is None:
            raise ImportError(
                "anthropic is required for Claude. Install with: pip install anthropic"
            )
        key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Get a key at https://console.anthropic.com/"
            )
        self._client = Anthropic(api_key=key)
        return self._client

    def complete(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ProviderResult:
        system_text, chat_messages = self._split_messages(messages)
        max_tokens = int(kwargs.pop("max_tokens", 1024))
        reserved = {"provider", "raise_on_block"}
        llm_kwargs = {k: v for k, v in kwargs.items() if k not in reserved}

        request: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": chat_messages,
            **llm_kwargs,
        }
        if system_text:
            request["system"] = system_text

        response = self.client.messages.create(**request)

        content = ""
        for block in response.content:
            if getattr(block, "type", None) == "text":
                content += block.text

        usage = getattr(response, "usage", None)
        return ProviderResult(
            content=content,
            raw_response=response,
            input_tokens=getattr(usage, "input_tokens", None) if usage else None,
            output_tokens=getattr(usage, "output_tokens", None) if usage else None,
        )

    @staticmethod
    def _split_messages(
        messages: list[dict[str, Any]],
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Split system prompts from user/assistant turns for Anthropic API."""
        system_parts: list[str] = []
        chat: list[dict[str, str]] = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if not isinstance(content, str):
                content = str(content)
            if role == "system":
                if content.strip():
                    system_parts.append(content)
            elif role in ("user", "assistant"):
                chat.append({"role": role, "content": content})

        if not chat:
            chat = [{"role": "user", "content": ""}]

        # Anthropic requires first message to be user
        if chat[0]["role"] != "user":
            chat.insert(0, {"role": "user", "content": "(context)"})

        return ("\n\n".join(system_parts) if system_parts else None, chat)
