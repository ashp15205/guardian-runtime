"""Google Gemini provider (free tier via Google AI Studio)."""
from __future__ import annotations

import os
from typing import Any

from guardian_runtime.providers.base import ProviderResult

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]


class GeminiProvider:
    """Wraps google-genai SDK for Gemini models."""

    name = "gemini"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._client = None

    def _resolve_api_key(self) -> str:
        key = self._api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        return key

    def _get_client(self):
        if self._client is None:
            if genai is None:
                raise ImportError(
                    "Google GenAI SDK not installed. Run: pip install guardian-runtime[google]"
                )
            self._client = genai.Client(api_key=self._resolve_api_key())
        return self._client

    def complete(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ProviderResult:
        client = self._get_client()

        # Extract system instruction
        system_parts = [
            m["content"] for m in messages
            if m.get("role") == "system" and m.get("content")
        ]
        system_instruction = "\n".join(system_parts) or None

        # Build contents for non-system messages
        contents = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if role not in ("user", "assistant") or not content:
                continue
            gemini_role = "user" if role == "user" else "model"
            contents.append(
                genai_types.Content(
                    role=gemini_role,
                    parts=[genai_types.Part(text=content)]
                )
            )

        if not contents:
            contents = [genai_types.Content(
                role="user",
                parts=[genai_types.Part(text="")]
            )]

        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        content = response.text or ""

        input_tokens: int | None = None
        output_tokens: int | None = None
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            input_tokens = getattr(usage, "prompt_token_count", None)
            output_tokens = getattr(usage, "candidates_token_count", None)

        return ProviderResult(
            content=content,
            raw_response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )