"""Token counting — tiktoken wrapper."""
from __future__ import annotations  # Python 3.9 compatibility
# TODO (Week 4): Implement token counting functions
# See ARCHITECTURE.md §4.5


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text for the given model using tiktoken."""
    raise NotImplementedError


def count_messages_tokens(messages: list[dict], model: str = "gpt-4") -> int:
    """Count total tokens for a list of chat messages including ChatML overhead."""
    raise NotImplementedError
