"""Input Guard — scans prompts before they reach the LLM."""
from __future__ import annotations

from guardian.core.models import GuardCheckResult, Violation
from guardian.core.policy import AgentPolicy, InputGuardConfig, PIIAction
from guardian.guards.validators.jailbreak import JailbreakDetector
from guardian.guards.validators.pii import PIIDetector, PIIType


def _entity_name_to_type(name: str) -> PIIType | None:
    mapping = {t.value: t for t in PIIType}
    return mapping.get(name)


class InputGuard:
    """Runs PII, secret, and jailbreak checks on user input."""

    def __init__(
        self,
        pii_detector: PIIDetector | None = None,
        jailbreak_detector: JailbreakDetector | None = None,
    ) -> None:
        self._jailbreak = jailbreak_detector or JailbreakDetector()

    def check(self, text: str, agent_policy: AgentPolicy) -> GuardCheckResult:
        config = agent_policy.input_guard or InputGuardConfig()
        violations: list[Violation] = []
        working_text = text

        if config.jailbreak_detection:
            jb = self._jailbreak.detect(text)
            if jb.is_jailbreak:
                violations.append(
                    Violation(
                        type="jailbreak",
                        severity="critical",
                        detail=f"Jailbreak pattern detected ({jb.category})",
                        action="blocked",
                        metadata={
                            "category": jb.category,
                            "pattern": jb.pattern_matched,
                        },
                    )
                )

        if config.pii_detection:
            enabled = self._enabled_pii_types(config)
            detector = PIIDetector(enabled_types=enabled)
            matches = detector.detect(text)

            for match in matches:
                is_secret = match.pii_type == PIIType.SECRET
                severity = "critical" if is_secret else "high"
                if is_secret and match.confidence < 0.9:
                    severity = "medium"

                v_type = "secret" if is_secret else "pii"
                action = self._action_for(config.pii_action)

                violations.append(
                    Violation(
                        type=v_type,
                        severity=severity,
                        detail=f"Detected {match.pii_type.value} in input",
                        action=action,
                        metadata={
                            "pii_type": match.pii_type.value,
                            "confidence": match.confidence,
                        },
                    )
                )

            if matches and config.pii_action == PIIAction.REDACT:
                working_text = detector.redact(text)

        blocking = any(v.action == "blocked" for v in violations)
        allowed = not blocking

        if config.pii_action == PIIAction.REDACT and violations and not blocking:
            return GuardCheckResult(
                allowed=True,
                violations=violations,
                processed_text=working_text,
            )

        return GuardCheckResult(allowed=allowed, violations=violations)

    def _enabled_pii_types(self, config: InputGuardConfig) -> list[PIIType]:
        types: list[PIIType] = []
        for name in config.pii_entities:
            pii_type = _entity_name_to_type(name)
            if pii_type is not None:
                types.append(pii_type)
        return types or list(PIIType)

    @staticmethod
    def _action_for(pii_action: PIIAction) -> str:
        if pii_action == PIIAction.BLOCK:
            return "blocked"
        if pii_action == PIIAction.FLAG:
            return "flagged"
        if pii_action == PIIAction.REDACT:
            return "redacted"
        return "blocked"
