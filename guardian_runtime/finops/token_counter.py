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
        text_content = messages_to_text(messages)
        return _word_estimate(text_content) + len(messages) * 4 + 2

    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens = 0
        for message in messages:
            tokens += 4
            content = message.get("content")
            if isinstance(content, str):
                tokens += len(encoding.encode(content))
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_val = block.get("text")
                        if isinstance(text_val, str):
                            tokens += len(encoding.encode(text_val))
        tokens += 2
        return tokens
    except Exception:
        text_content = messages_to_text(messages)
        return _word_estimate(text_content) + len(messages) * 4 + 2


def messages_to_text(messages: list[dict]) -> str:
    """Concatenate message contents for guard scanning."""
    parts: list[str] = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_val = block.get("text")
                    if isinstance(text_val, str) and text_val.strip():
                        parts.append(text_val)
    return "\n".join(parts)