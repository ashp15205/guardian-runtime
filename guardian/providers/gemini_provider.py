"""Google Gemini provider (free tier via Google AI Studio)."""
from __future__ import annotations

import os
from typing import Any

from guardian.providers.base import ProviderResult

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore[assignment]


class GeminiProvider:
    """Wraps google-generativeai for Gemini models."""

    name = "gemini"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def _resolve_api_key(self) -> str:
        key = self._api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        return key

    def complete(
        self,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ProviderResult:
        if genai is None:
            raise ImportError(
                "google-generativeai is required for Gemini. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=self._resolve_api_key())

        system_instruction = "\n".join(
            m["content"] for m in messages if m.get("role") == "system" and m.get("content")
        )
        system_instruction = system_instruction or None

        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction,
        )

        chat_messages: list[dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if role not in ("user", "assistant") or not content:
                continue
            gemini_role = "user" if role == "user" else "model"
            chat_messages.append({"role": gemini_role, "parts": [content]})

        generation_config = kwargs.get("generation_config")
        gen_kwargs: dict[str, Any] = {}
        if generation_config is not None:
            gen_kwargs["generation_config"] = generation_config

        if not chat_messages:
            response = gemini_model.generate_content("", **gen_kwargs)
        elif len(chat_messages) == 1:
            response = gemini_model.generate_content(chat_messages[0]["parts"][0], **gen_kwargs)
        else:
            history = chat_messages[:-1]
            last_message = chat_messages[-1]["parts"][0]
            chat = gemini_model.start_chat(history=history)
            response = chat.send_message(last_message, **gen_kwargs)

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
