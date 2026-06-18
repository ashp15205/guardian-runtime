"""File Interceptor — scans code files for secrets and converts documents to Markdown."""
from __future__ import annotations

import base64
import mimetypes
import os
import tempfile
import uuid
from dataclasses import dataclass
from typing import Any

from guardian_runtime.core.models import GuardianRuntimeBlockedError, GuardianRuntimeResponse, Violation
from guardian_runtime.guards.validators.pii import PIIDetector, PIIType

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

CODE_EXTS = {".env", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".sh", ".config", ".txt"}
DOC_EXTS = {".pdf", ".docx", ".html", ".xlsx", ".csv"}

# In user request, .txt was listed under docs/text, but it could be code or doc. Let's put .txt in DOC_EXTS so MarkItDown handles it, or just decode it.
CODE_EXTS = {".env", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".sh", ".config"}
DOC_EXTS = {".pdf", ".docx", ".html", ".xlsx", ".txt"}

@dataclass
class InterceptResult:
    messages: list[dict[str, Any]]
    violations: list[Violation]
    conversions: int


class FileInterceptor:
    def __init__(self):
        self.secret_detector = PIIDetector(enabled_types=[PIIType.SECRET])

    def _get_extension_from_mime(self, mime_type: str) -> str:
        if mime_type == "application/pdf":
            return ".pdf"
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return ".docx"
        if mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return ".xlsx"
        if mime_type == "text/html":
            return ".html"
        if mime_type == "text/plain":
            return ".txt"
        
        # Mimetypes fallback
        ext = mimetypes.guess_extension(mime_type)
        return ext.lower() if ext else ""

    def process_messages(self, messages: list[dict[str, Any]]) -> InterceptResult:
        violations: list[Violation] = []
        conversions = 0
        new_messages = []

        for msg in messages:
            if not isinstance(msg, dict):
                new_messages.append(msg)
                continue
                
            role = msg.get("role")
            content = msg.get("content")
            
            if not content or isinstance(content, str):
                new_messages.append(msg)
                continue
                
            if not isinstance(content, list):
                new_messages.append(msg)
                continue
                
            new_content = []
            for part in content:
                if not isinstance(part, dict):
                    new_content.append(part)
                    continue

                part_type = part.get("type")
                
                # Handling Anthropic document or image types
                if part_type in ("document", "image") and "source" in part:
                    source = part["source"]
                    if isinstance(source, dict) and source.get("type") == "base64":
                        mime = source.get("media_type", "")
                        b64_data = source.get("data", "")
                        ext = self._get_extension_from_mime(mime)
                        
                        part_res, part_vio, part_conv = self._process_file_part(ext, b64_data)
                        if part_vio:
                            violations.extend(part_vio)
                        if part_conv:
                            conversions += part_conv
                        
                        if part_res is not None:
                            new_content.append(part_res)
                        else:
                            new_content.append(part)
                        continue

                # Handling OpenAI image_url types
                elif part_type == "image_url" and "image_url" in part:
                    url = part["image_url"].get("url", "")
                    if url.startswith("data:"):
                        # parse data URI
                        # Format: data:[<mediatype>][;base64],<data>
                        header, b64_data = url.split(",", 1)
                        mime = header.replace("data:", "").replace(";base64", "")
                        ext = self._get_extension_from_mime(mime)
                        
                        part_res, part_vio, part_conv = self._process_file_part(ext, b64_data)
                        if part_vio:
                            violations.extend(part_vio)
                        if part_conv:
                            conversions += part_conv
                        
                        if part_res is not None:
                            new_content.append(part_res)
                        else:
                            new_content.append(part)
                        continue
                
                new_content.append(part)
            
            new_msg = dict(msg)
            new_msg["content"] = new_content
            new_messages.append(new_msg)

        return InterceptResult(
            messages=new_messages,
            violations=violations,
            conversions=conversions
        )

    def _process_file_part(self, ext: str, b64_data: str) -> tuple[dict[str, Any] | None, list[Violation], int]:
        """Returns new content part dict, violations list, conversions count."""
        try:
            raw_bytes = base64.b64decode(b64_data)
        except Exception:
            # If we can't decode, just ignore
            return None, [], 0

        # Code files -> Secret Scan
        if ext in CODE_EXTS:
            try:
                text_content = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_content = raw_bytes.decode("latin-1")
            
            matches = self.secret_detector.detect(text_content)
            if matches:
                types = ", ".join({m.pii_type.value for m in matches})
                v = Violation(
                    type="secret",
                    severity="critical",
                    detail=f"Secret detected in file attachment ({ext}): {types}",
                    action="blocked"
                )
                return None, [v], 0
            
            return None, [], 0
            
        # Doc files -> MarkItDown
        if ext in DOC_EXTS:
            if not MarkItDown:
                # If MarkItDown isn't installed, fail conversion
                v = Violation(
                    type="conversion_failed",
                    severity="critical",
                    detail=f"Could not convert file {ext}. Reason: markitdown package not installed.",
                    action="blocked"
                )
                return None, [v], 0

            # Write to temp file
            filename = f"temp_{uuid.uuid4().hex}{ext}"
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            
            try:
                with open(temp_path, "wb") as f:
                    f.write(raw_bytes)
                
                md = MarkItDown()
                result = md.convert(temp_path)
                md_text = result.text_content
                
                # Token estimation: rough approximation (4 chars = 1 token)
                approx_tokens = len(md_text) // 4
                
                system_msg = f"[Guardian: converted {ext} → Markdown, ~{approx_tokens} tokens]\n{md_text}"
                
                return {"type": "text", "text": system_msg}, [], 1
                
            except Exception as e:
                v = Violation(
                    type="conversion_failed",
                    severity="critical",
                    detail=f"Could not convert file {ext}. Reason: {str(e)}. Please convert manually and paste the text.",
                    action="blocked"
                )
                return None, [v], 0
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        
        return None, [], 0
