"""LLM provider interface for GuardianRuntime Runtime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ProviderResult:
    """Normalized result from any LLM provider."""

    content: str
    raw_response: Any
    input_tokens: int | None = None
    output_tokens: int | None = None


class ChatProvider(Protocol):
    """Provider that runs a chat-style completion."""

    name: str

    def complete(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ProviderResult:
        """Run chat completion and return normalized text + optional token usage."""

    def stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        """Yield text chunks and return ProviderResult at the end."""


DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-3-5-haiku-latest",
}
