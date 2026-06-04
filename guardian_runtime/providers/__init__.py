"""LLM provider registry for GuardianRuntime Runtime."""

from guardian_runtime.providers.anthropic_provider import AnthropicProvider
from guardian_runtime.providers.base import DEFAULT_MODELS, ChatProvider, ProviderResult
from guardian_runtime.providers.gemini_provider import GeminiProvider
from guardian_runtime.providers.openai_provider import OpenAIProvider

_PROVIDERS: dict[str, type] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
}


def get_provider(name: str, **kwargs) -> ChatProvider:
    """Return a provider instance by name (`openai`, `gemini`, or `anthropic`)."""
    key = name.lower().strip()
    if key not in _PROVIDERS:
        raise ValueError(f"Unknown provider {name!r}. Supported: {sorted(_PROVIDERS)}")
    return _PROVIDERS[key](**kwargs)


def default_model(provider: str) -> str:
    """Default model id for a provider."""
    key = provider.lower().strip()
    if key not in DEFAULT_MODELS:
        raise ValueError(f"Unknown provider {provider!r}")
    return DEFAULT_MODELS[key]


def supported_providers() -> list[str]:
    return sorted(_PROVIDERS.keys())


__all__ = [
    "ChatProvider",
    "ProviderResult",
    "OpenAIProvider",
    "GeminiProvider",
    "AnthropicProvider",
    "get_provider",
    "default_model",
    "supported_providers",
    "DEFAULT_MODELS",
]
