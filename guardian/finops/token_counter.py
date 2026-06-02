"""Token counting — tiktoken wrapper."""
from __future__ import annotations

import tiktoken


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text for the given model using tiktoken."""
    if not text:
        return 0
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def count_messages_tokens(messages: list[dict], model: str = "gpt-4o") -> int:
    """Count total tokens for chat messages including ChatML overhead."""
    if not messages:
        return 0

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = 0
    for message in messages:
        tokens += 4  # role framing overhead per message
        for value in message.values():
            if isinstance(value, str):
                tokens += len(encoding.encode(value))
    tokens += 2  # assistant reply priming
    return tokens


def messages_to_text(messages: list[dict]) -> str:
    """Concatenate message contents for guard scanning."""
    parts: list[str] = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content)
    return "\n".join(parts)
