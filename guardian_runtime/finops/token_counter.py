"""Token counting — tiktoken with fallback for non-OpenAI models."""
from __future__ import annotations


def _word_estimate(text: str) -> int:
    """Fallback: estimate tokens as ~1.3x word count."""
    return max(1, int(len(text.split()) * 1.3))


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text. Uses tiktoken for OpenAI models, estimates for others."""
    if not text:
        return 0

    # Non-OpenAI models — use word estimate (no tiktoken encoding available)
    non_openai = ("gemini", "claude", "anthropic", "llama", "mistral")
    if any(m in model.lower() for m in non_openai):
        return _word_estimate(text)

    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return _word_estimate(text)


def count_messages_tokens(messages: list[dict], model: str = "gpt-4o") -> int:
    """Count total tokens for chat messages including overhead."""
    if not messages:
        return 0

    non_openai = ("gemini", "claude", "anthropic", "llama", "mistral")
    use_estimate = any(m in model.lower() for m in non_openai)

    if use_estimate:
        total = sum(
            _word_estimate(v)
            for msg in messages
            for v in msg.values()
            if isinstance(v, str)
        )
        return total + len(messages) * 4 + 2

    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens = 0
        for message in messages:
            tokens += 4
            for value in message.values():
                if isinstance(value, str):
                    tokens += len(encoding.encode(value))
        tokens += 2
        return tokens
    except Exception:
        total = sum(
            _word_estimate(v)
            for msg in messages
            for v in msg.values()
            if isinstance(v, str)
        )
        return total + len(messages) * 4 + 2


def messages_to_text(messages: list[dict]) -> str:
    """Concatenate message contents for guard scanning."""
    parts: list[str] = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content)
    return "\n".join(parts)