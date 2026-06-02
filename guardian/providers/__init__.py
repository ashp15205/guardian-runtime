"""LLM provider registry for Guardian Runtime."""

from guardian.providers.base import DEFAULT_MODELS, ChatProvider, ProviderResult
from guardian.providers.gemini_provider import GeminiProvider
from guardian.providers.openai_provider import OpenAIProvider

_PROVIDERS: dict[str, type] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str, **kwargs) -> ChatProvider:
    """Return a provider instance by name (`openai` or `gemini`)."""
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


__all__ = [
    "ChatProvider",
    "ProviderResult",
    "OpenAIProvider",
    "GeminiProvider",
    "get_provider",
    "default_model",
    "DEFAULT_MODELS",
]
