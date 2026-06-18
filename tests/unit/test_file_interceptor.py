import base64
import json
import pytest
from unittest.mock import patch, MagicMock

from guardian_runtime.core.file_interceptor import FileInterceptor

@pytest.fixture
def interceptor():
    return FileInterceptor()

def test_code_file_with_secret_blocked(interceptor):
    # AWS access key (AKIA...)
    secret_env_content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
    b64_content = base64.b64encode(secret_env_content.encode("utf-8")).decode("utf-8")
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "text/plain", # Fallback or any type
                        "data": b64_content
                    }
                }
            ]
        }
    ]
    
    # We monkeypatch the _get_extension_from_mime to return .env for this test
    with patch.object(interceptor, '_get_extension_from_mime', return_value='.env'):
        result = interceptor.process_messages(messages)
        
    assert len(result.violations) > 0
    assert result.violations[0].type == "secret"
    assert "AKIAIOSFODNN7EXAMPLE" not in result.messages[0]["content"][0] # original content shouldn't be passed

@patch('guardian_runtime.core.file_interceptor.MarkItDown')
def test_doc_file_converted(mock_markitdown, interceptor):
    # Simulate a PDF base64 payload
    pdf_content = b"%PDF-1.4 mock content"
    b64_content = base64.b64encode(pdf_content).decode("utf-8")
    
    mock_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.text_content = "Mock Markdown Content"
    mock_instance.convert.return_value = mock_result
    mock_markitdown.return_value = mock_instance
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:application/pdf;base64,{b64_content}"
                    }
                }
            ]
        }
    ]
    
    result = interceptor.process_messages(messages)
    
    assert len(result.violations) == 0
    assert result.conversions == 1
    
    processed_content = result.messages[0]["content"][0]
    assert processed_content["type"] == "text"
    assert "Mock Markdown Content" in processed_content["text"]
    assert "[Guardian: converted .pdf \u2192 Markdown" in processed_content["text"]

@patch('guardian_runtime.core.file_interceptor.MarkItDown')
def test_conversion_failure_blocks_request(mock_markitdown, interceptor):
    pdf_content = b"%PDF-1.4 corrupt content"
    b64_content = base64.b64encode(pdf_content).decode("utf-8")
    
    mock_instance = MagicMock()
    mock_instance.convert.side_effect = Exception("File is corrupt")
    mock_markitdown.return_value = mock_instance
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:application/pdf;base64,{b64_content}"
                    }
                }
            ]
        }
    ]
    
    result = interceptor.process_messages(messages)
    
    assert len(result.violations) > 0
    assert result.violations[0].type == "conversion_failed"
    assert result.violations[0].severity == "critical"
    assert "File is corrupt" in result.violations[0].detail
    assert result.conversions == 0
