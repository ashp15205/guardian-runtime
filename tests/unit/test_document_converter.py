"""Unit tests for DocumentConverter."""
import pytest
from unittest.mock import MagicMock, patch

from guardian_runtime.optimizer.document_converter import DocumentConverter

@patch("guardian_runtime.optimizer.document_converter.MARKITDOWN_AVAILABLE", True)
def test_convert_document_raises_if_not_found():
    import guardian_runtime.optimizer.document_converter as dc
    dc.MarkItDown = MagicMock()
    
    converter = dc.DocumentConverter()
    with pytest.raises(FileNotFoundError):
        converter.convert("does_not_exist.pdf")
        
    del dc.MarkItDown

@patch("guardian_runtime.optimizer.document_converter.MARKITDOWN_AVAILABLE", True)
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.stat")
def test_convert_document_success(mock_stat, mock_exists):
    # We must patch MarkItDown inside the module since it wasn't imported
    # due to the ImportError in reality.
    mock_stat.return_value.st_size = 1024
    
    mock_md_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.text_content = "# Mocked Markdown Content"
    mock_md_instance.convert.return_value = mock_result
    
    # Temporarily inject the mock class into the module
    import guardian_runtime.optimizer.document_converter as dc
    dc.MarkItDown = MagicMock(return_value=mock_md_instance)

    converter = dc.DocumentConverter()
    
    # We mock path ops so "dummy.pdf" is technically found
    result = converter.convert("dummy.pdf")
    
    assert result.markdown == "# Mocked Markdown Content"
    assert result.original_size_bytes == 1024
    assert result.markdown_tokens > 0
    assert result.format_detected == "pdf"
    
    # Cleanup
    del dc.MarkItDown
