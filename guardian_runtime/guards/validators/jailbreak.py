"""Jailbreak and prompt injection detector — regex patterns, zero external deps."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class JailbreakResult:
    is_jailbreak: bool
    confidence: float
    pattern_matched: str | None
    category: str | None  # dan | instruction_override | role_play | encoding | extraction


# (regex_pattern, category)
JAILBREAK_PATTERNS: list[tuple[str, str]] = [
    # DAN variants
    (r"do anything now", "dan"),
    (r"\bDAN\b", "dan"),
    (r"DAN mode", "dan"),
    (r"developer mode enabled", "dan"),
    (r"jailbreak mode", "dan"),
    (r"you are now in .* mode", "dan"),
    (r"enable .* mode", "dan"),
    (r"unrestricted mode", "dan"),
    # Instruction override
    (r"ignore (?:all )?(?:previous|prior|above) instructions?", "instruction_override"),
    (r"ignore (?:your|the) system prompt", "instruction_override"),
    (r"forget everything (?:you were|you've been) told", "instruction_override"),
    (r"forget (?:all )?(?:previous|prior) (?:instructions|rules)", "instruction_override"),
    (r"disregard (?:all )?(?:previous|prior|your) instructions?", "instruction_override"),
    (r"override (?:the )?system prompt", "instruction_override"),
    (r"new instructions\s*:", "instruction_override"),
    (r"do not follow (?:your|the) (?:rules|guidelines|instructions)", "instruction_override"),
    (r"bypass (?:your|all|the) (?:rules|restrictions|filters|safety)", "instruction_override"),
    (r"you must ignore (?:all )?(?:previous|safety)", "instruction_override"),
    # Role play injection
    (r"pretend you are an? unrestricted", "role_play"),
    (r"act as (?:an? )?(?:unrestricted|uncensored|unfiltered)", "role_play"),
    (r"you are now free from all guidelines", "role_play"),
    (r"roleplay as (?:an? )?(?:evil|malicious|unrestricted)", "role_play"),
    (r"simulate (?:an? )?(?:AI|assistant) (?:without|with no) (?:rules|restrictions)", "role_play"),
    (r"you are (?:no longer|not) bound by", "role_play"),
    (r"behave as if you have no (?:rules|restrictions|guidelines)", "role_play"),
    (r"from now on you (?:will|must|should) (?:ignore|disregard)", "role_play"),
    # Encoding tricks
    (r"decode this base64", "encoding"),
    (r"decode (?:the following )?(?:base64|hex|rot13)", "encoding"),
    (r"base64\s*(?:encoded|decode)", "encoding"),
    (r"execute (?:the )?(?:following )?encoded", "encoding"),
    (r"\\x[0-9a-f]{2}", "encoding"),
    # System prompt extraction
    (r"reveal your system prompt", "extraction"),
    (r"show (?:me )?your (?:system )?instructions", "extraction"),
    (r"what are your (?:system )?instructions", "extraction"),
    (r"repeat (?:your )?(?:system )?prompt verbatim", "extraction"),
    (r"print (?:your )?(?:initial|system) (?:prompt|instructions)", "extraction"),
    (r"output (?:your )?(?:hidden|system) (?:prompt|instructions)", "extraction"),
]


class JailbreakDetector:
    """Detects jailbreak attempts using compiled regex patterns."""

    def __init__(self) -> None:
        self._compiled = [
            (re.compile(pattern, re.IGNORECASE), category, pattern)
            for pattern, category in JAILBREAK_PATTERNS
        ]

    def detect(self, text: str) -> JailbreakResult:
        """Return first matching jailbreak pattern, or is_jailbreak=False."""
        if not text:
            return JailbreakResult(False, 0.0, None, None)

        for compiled, category, raw in self._compiled:
            if compiled.search(text):
                return JailbreakResult(
                    is_jailbreak=True,
                    confidence=0.85,
                    pattern_matched=raw,
                    category=category,
                )

        return JailbreakResult(False, 0.0, None, None)
