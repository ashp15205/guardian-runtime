"""Output Guard — scans LLM responses before they reach the user."""
from __future__ import annotations

from guardian_runtime.core.models import GuardCheckResult, Violation
from guardian_runtime.core.policy import AgentPolicy, OutputGuardConfig
from guardian_runtime.guards.validators.pii import PIIDetector, PIIType


class OutputGuard:
    """Runs PII and secret checks on LLM output."""

    def check(self, text: str, agent_policy: AgentPolicy) -> GuardCheckResult:
        config = agent_policy.output_guard or OutputGuardConfig()
        violations: list[Violation] = []

        if not config.scanner_enabled:
            return GuardCheckResult(allowed=True)


        detector = PIIDetector()
        matches = detector.detect(text)

        for match in matches:
            is_secret = match.pii_type == PIIType.SECRET
            violations.append(
                Violation(
                    type="secret" if is_secret else "output_pii",
                    severity="critical" if is_secret else "high",
                    detail=f"Detected {match.pii_type.value} in model output",
                    action="flagged",
                    metadata={"pii_type": match.pii_type.value},
                )
            )

        blocking = any(v.action == "blocked" for v in violations)
        return GuardCheckResult(allowed=not blocking, violations=violations)
