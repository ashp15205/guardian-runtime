"""Jailbreak and prompt injection detector — 50+ patterns, zero external deps."""
from __future__ import annotations  # Python 3.9 compatibility
# TODO (Week 4): Implement JailbreakDetector
# See ARCHITECTURE.md §4.3.2

import re
from dataclasses import dataclass


@dataclass
class JailbreakResult:
    is_jailbreak: bool
    confidence: float
    pattern_matched: str | None
    category: str | None  # "dan" | "instruction_override" | "role_play" | "encoding" | "extraction"


# TODO (Week 4): Fill in all 50+ patterns from ARCHITECTURE.md §4.3.2
JAILBREAK_PATTERNS: list[tuple[str, str]] = []


class JailbreakDetector:
    """Detects jailbreak attempts using compiled regex patterns."""

    def __init__(self):
        self._compiled = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in JAILBREAK_PATTERNS
        ]

    def detect(self, text: str) -> JailbreakResult:
        """Return first matching jailbreak pattern, or is_jailbreak=False."""
        raise NotImplementedError
