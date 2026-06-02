"""Document to Markdown converter using Microsoft MarkItDown."""
from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

from guardian.optimizer.models import ConversionResult
from guardian.finops.token_counter import count_tokens


class DocumentConverter:
    """Converts files to Markdown to save LLM tokens using MarkItDown."""

    def __init__(self) -> None:
        if not MARKITDOWN_AVAILABLE:
            raise ImportError(
                "markitdown is not installed. Please install guardian-runtime with markitdown dependency."
            )
        self.md = MarkItDown()

    def convert(self, path: str | Path) -> ConversionResult:
        """Convert a local file to markdown."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        size = path.stat().st_size
        extension = path.suffix.lower().lstrip(".")
        
        try:
            result = self.md.convert(str(path))
            content = result.text_content
        except Exception as e:
            # Fallback if markitdown fails
            raise RuntimeError(f"MarkItDown conversion failed: {e}") from e

        tokens = count_tokens(content)
        return ConversionResult(
            markdown=content,
            original_size_bytes=size,
            markdown_tokens=tokens,
            format_detected=extension,
            warnings=[]
        )

    def convert_stream(self, stream: BinaryIO, filename: str) -> ConversionResult:
        """Convert from an open file stream."""
        raise NotImplementedError("Stream conversion via markitdown requires writing to a temp file currently or using its streaming API if available.")
