"""
GuardianRuntime Runtime — Local-first AI governance layer.

Usage:
    from guardian_runtime import GuardianRuntime

    guardian_runtime = GuardianRuntime.from_policy("policy.yaml")
    response = guardian_runtime.complete(model="gpt-4", messages=[...])
"""
from __future__ import annotations  # Python 3.9 compatibility

from guardian_runtime.core.engine import GuardianRuntimeEngine
from guardian_runtime.core.models import GuardianRuntimeBlockedError, GuardCheckResult, GuardianRuntimeResponse, Violation
from guardian_runtime.core.policy import load_policy, OptimizerConfig
from guardian_runtime.optimizer import DocumentConverter, InputOptimizer, OptimizeResult, ConversionResult

# Version matches pyproject.toml
__version__ = "1.1.4"
__all__ = [
    "GuardianRuntime",
    "GuardianRuntimeEngine",
    "GuardianRuntimeBlockedError",
    "GuardianRuntimeResponse",
    "Violation",
    "GuardCheckResult",
    "scan_pii",
    "scan_secrets",
    "optimize_input",
    "convert_document",
    "__version__",
]


class GuardianRuntime:
    """Main entry point for GuardianRuntime Runtime."""

    def __init__(self, engine: GuardianRuntimeEngine | None = None):
        if engine is None:
            from guardian_runtime.core.policy import Policy
            engine = GuardianRuntimeEngine(Policy())
        self._engine = engine

    @classmethod
    def from_policy(cls, path: str) -> "GuardianRuntime":
        """Load a GuardianRuntime instance from a YAML policy file."""
        policy = load_policy(path)
        engine = GuardianRuntimeEngine(policy)
        return cls(engine)

    def complete(
        self,
        model: str | None = None,
        messages: list | None = None,
        agent_id: str = "default",
        session_id: str | None = None,
        provider: str | None = None,
        **kwargs,
    ):
        """Wrap an LLM call with full GuardianRuntime governance."""
        return self._engine.complete(
            model=model,
            messages=messages,
            agent_id=agent_id,
            session_id=session_id,
            provider=provider,
            **kwargs,
        )

    def get_cost_report(self, agent_id: str = "default") -> dict:
        """Return cost report for the given agent."""
        return self._engine.get_cost_report(agent_id)


# ---------------------------------------------------------------------------
# Convenience wrappers for quickstart (v0.1.0)
# ---------------------------------------------------------------------------

class ScanResult:
    """Simple result object for the convenience scanner functions."""
    def __init__(self, blocked: bool, type: str, severity: str):
        self.blocked = blocked
        self.type = type
        self.severity = severity


def scan_pii(text: str) -> ScanResult:
    """Convenience function to scan for PII."""
    from guardian_runtime.guards.validators.pii import PIIDetector, PIIType
    detector = PIIDetector()
    
    # We ignore secrets for the pii scan specifically
    matches = [m for m in detector.detect(text) if m.pii_type != PIIType.SECRET]
    
    if matches:
        return ScanResult(
            blocked=True,
            type=matches[0].pii_type.name.upper(),
            severity="HIGH"
        )
    return ScanResult(blocked=False, type="NONE", severity="NONE")


def scan_secrets(text: str) -> ScanResult:
    """Convenience function to scan for secrets."""
    from guardian_runtime.guards.validators.pii import PIIDetector, PIIType
    detector = PIIDetector()
    
    matches = [m for m in detector.detect(text) if m.pii_type == PIIType.SECRET]
    
    if matches:
        match = matches[0]
        # Our PII detector returns high/medium confidence
        severity = "HIGH" if match.confidence >= 0.9 else "MEDIUM"
        return ScanResult(
            blocked=True,
            type="SECRET_KEY",
            severity=severity
        )
    return ScanResult(blocked=False, type="NONE", severity="NONE")


def optimize_input(messages: list[dict], config: OptimizerConfig | None = None, model: str = "gpt-4o") -> OptimizeResult:
    """Convenience function: optimize prompts to reduce tokens."""
    cfg = config or OptimizerConfig(enabled=True)
    optimizer = InputOptimizer(cfg)
    return optimizer.optimize(messages, model)

def convert_document(path: str) -> ConversionResult:
    """Convenience function: convert PDF/DOCX to Markdown for token savings."""
    converter = DocumentConverter()
    return converter.convert(path)

