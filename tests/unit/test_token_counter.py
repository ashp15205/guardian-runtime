"""Tests for token counting and cost estimation."""

from guardian_runtime.finops.cost_calculator import estimate_cost
from guardian_runtime.finops.token_counter import count_messages_tokens, count_tokens


def test_count_tokens_nonzero():
    assert count_tokens("hello world", model="gpt-4o-mini") > 0


def test_count_messages_tokens():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]
    assert count_messages_tokens(messages, model="gpt-4o-mini") > 0


def test_count_tokens_gemini_uses_estimate():
    """Gemini models skip tiktoken — word-based estimate."""
    assert count_tokens("hello world foo bar", model="gemini-2.0-flash") >= 4


def test_count_messages_tokens_claude_uses_estimate():
    messages = [{"role": "user", "content": "Hello there"}]
    assert count_messages_tokens(messages, model="claude-3-5-haiku-latest") > 0


def test_estimate_cost():
    cost = estimate_cost(1000, 500, model="gpt-4o-mini")
    assert cost > 0
