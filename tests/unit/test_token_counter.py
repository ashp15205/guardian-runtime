"""Tests for token counting and cost estimation."""

from guardian.finops.cost_calculator import estimate_cost
from guardian.finops.token_counter import count_messages_tokens, count_tokens


def test_count_tokens_nonzero():
    assert count_tokens("hello world", model="gpt-4o-mini") > 0


def test_count_messages_tokens():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]
    assert count_messages_tokens(messages, model="gpt-4o-mini") > 0


def test_estimate_cost():
    cost = estimate_cost(1000, 500, model="gpt-4o-mini")
    assert cost > 0
