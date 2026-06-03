"""Tests for LLM providers."""

from unittest.mock import MagicMock, patch

import pytest

from guardian.providers import default_model, get_provider, supported_providers
from guardian.providers.openai_provider import OpenAIProvider


def test_supported_providers():
    assert supported_providers() == ["anthropic", "gemini", "openai"]


def test_default_models():
    assert default_model("openai") == "gpt-4o-mini"
    assert default_model("gemini") == "gemini-2.0-flash"
    assert default_model("anthropic") == "claude-3-5-haiku-latest"


def test_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("azure")


def test_openai_provider_with_mock_client():
    mock_client = MagicMock()
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="Hi"))]
    completion.usage = MagicMock(prompt_tokens=3, completion_tokens=2)
    mock_client.chat.completions.create.return_value = completion

    provider = OpenAIProvider(client=mock_client)
    result = provider.complete(
        "gpt-4o-mini",
        [{"role": "user", "content": "Hello"}],
    )
    assert result.content == "Hi"
    assert result.input_tokens == 3


@patch("guardian.providers.gemini_provider.genai")
def test_gemini_provider_single_message(mock_genai):
    mock_response = MagicMock()
    mock_response.text = "Hello from Gemini"
    mock_response.usage_metadata = MagicMock(prompt_token_count=4, candidates_token_count=2)

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    from guardian.providers.gemini_provider import GeminiProvider

    provider = GeminiProvider(api_key="test-key")
    result = provider.complete(
        "gemini-2.0-flash",
        [{"role": "user", "content": "Hi"}],
    )

    assert result.content == "Hello from Gemini"
    assert result.input_tokens == 4
    mock_genai.configure.assert_called_once()


def test_anthropic_provider_with_mock_client():
    mock_client = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Hello from Claude"
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.usage = MagicMock(input_tokens=5, output_tokens=3)
    mock_client.messages.create.return_value = mock_response

    from guardian.providers.anthropic_provider import AnthropicProvider

    provider = AnthropicProvider(client=mock_client)
    result = provider.complete(
        "claude-3-5-haiku-latest",
        [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hi"},
        ],
    )
    assert result.content == "Hello from Claude"
    assert result.input_tokens == 5
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["system"] == "Be concise."
