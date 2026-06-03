"""Document to Markdown converter using Microsoft MarkItDown."""
from __future__ import annotations

import os
import tempfile
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
    """Converts PDF/DOCX/XLSX and other files to Markdown to save LLM tokens."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".xls", ".html", ".htm", ".txt", ".md"}

    def __init__(self) -> None:
        if not MARKITDOWN_AVAILABLE:
            raise ImportError(
                "markitdown is not installed. Run: pip install guardian-runtime[optimizer]"
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
            raise RuntimeError(f"MarkItDown conversion failed: {e}") from e

        tokens = count_tokens(content)
        return ConversionResult(
            markdown=content,
            original_size_bytes=size,
            markdown_tokens=tokens,
            format_detected=extension,
            warnings=[],
        )

    def convert_stream(self, stream: BinaryIO, filename: str) -> ConversionResult:
        """Convert from an open file stream (writes temp file for MarkItDown)."""
        suffix = Path(filename).suffix or ".bin"
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(stream.read())
                tmp_path = tmp.name
            return self.convert(tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
