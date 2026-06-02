"""Tests for LLM providers."""

from unittest.mock import MagicMock, patch

import pytest

from guardian.providers import default_model, get_provider
from guardian.providers.openai_provider import OpenAIProvider


def test_default_models():
    assert default_model("openai") == "gpt-4o-mini"
    assert default_model("gemini") == "gemini-2.0-flash"


def test_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("anthropic")


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
