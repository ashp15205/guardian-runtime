"""Per-model cost tables and cost estimation."""
from __future__ import annotations

# Cost per 1,000 tokens in USD
MODEL_COST_PER_1K: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "gemini-1-5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1-5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-flash-lite": {"input": 0.0, "output": 0.0},
}


def estimate_cost(input_tokens: int, output_tokens: int = 0, model: str = "gpt-4o") -> float:
    """Estimate cost in USD for given token counts and model."""
    rates = MODEL_COST_PER_1K.get(model)
    if rates is None:
        # Prefix match for dated model names e.g. gpt-4o-2024-08-06
        for key, value in MODEL_COST_PER_1K.items():
            if model.startswith(key):
                rates = value
                break
    if rates is None:
        rates = MODEL_COST_PER_1K["gpt-4o-mini"]

    input_cost = (input_tokens / 1000.0) * rates["input"]
    output_cost = (output_tokens / 1000.0) * rates["output"]
    return round(input_cost + output_cost, 6)


def get_supported_models() -> list[str]:
    return list(MODEL_COST_PER_1K.keys())
