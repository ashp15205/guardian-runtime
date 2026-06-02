"""Optimizer data models for Guardian Runtime."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OptimizeResult:
    """Result of prompt optimization."""
    optimized_messages: list[dict]
    original_tokens: int
    optimized_tokens: int
    savings_pct: float
    actions_taken: list[str] = field(default_factory=list)
    estimated_cost_saved: float = 0.0
    guidance: list[str] = field(default_factory=list)


@dataclass
class ConversionResult:
    """Result of document to markdown conversion."""
    markdown: str
    original_size_bytes: int
    markdown_tokens: int
    format_detected: str
    warnings: list[str] = field(default_factory=list)
