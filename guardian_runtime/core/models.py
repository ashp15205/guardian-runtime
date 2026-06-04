"""Core data models for GuardianRuntime Runtime pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Violation:
    """A single policy violation detected during a guard check."""

    type: str  # pii, secret, jailbreak, token_limit, usage_limit, output_pii
    severity: str  # low, medium, high, critical
    detail: str
    action: str = "blocked"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GuardCheckResult:
    """Result of an input or output guard scan."""

    allowed: bool
    violations: list[Violation] = field(default_factory=list)
    processed_text: Optional[str] = None  # redacted text when action is redact


@dataclass
class GuardianRuntimeResponse:
    """Return value from GuardianRuntimeEngine.complete()."""

    content: str
    blocked: bool
    violations: list[Violation] = field(default_factory=list)
    model: Optional[str] = None
    provider: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    # Optimizer metadata
    optimization: dict | None = None
    raw_response: Any = None


class GuardianRuntimeBlockedError(Exception):
    """Raised when a call is blocked and raise_on_block=True."""

    def __init__(self, response: GuardianRuntimeResponse):
        self.response = response
        types = ", ".join(v.type for v in response.violations) or "unknown"
        super().__init__(f"GuardianRuntime blocked request: {types}")
