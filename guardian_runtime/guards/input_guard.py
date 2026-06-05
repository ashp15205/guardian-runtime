"""Input Guard — scans prompts before they reach the LLM."""
from __future__ import annotations

from guardian_runtime.core.models import GuardCheckResult, Violation
from guardian_runtime.core.policy import AgentPolicy, InputGuardConfig, ScannerAction
from guardian_runtime.guards.validators.jailbreak import JailbreakDetector
from guardian_runtime.guards.validators.pii import PIIDetector, PIIType


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

        if config.scanner_enabled:
            enabled = self._enabled_entities(config)
            detector = PIIDetector(enabled_types=enabled)
            matches = detector.detect(text)

            for match in matches:
                is_secret = match.pii_type == PIIType.SECRET
                severity = "critical" if is_secret else "high"
                if is_secret and match.confidence < 0.9:
                    severity = "medium"

                v_type = "secret" if is_secret else "pii"
                action = self._action_for(config.scanner_action)

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

            if matches and config.scanner_action == ScannerAction.REDACT:
                working_text = detector.redact(text)

        blocking = any(v.action == "blocked" for v in violations)
        allowed = not blocking

        if config.scanner_action == ScannerAction.REDACT and violations and not blocking:
            return GuardCheckResult(
                allowed=True,
                violations=violations,
                processed_text=working_text,
            )

        return GuardCheckResult(allowed=allowed, violations=violations)

    def _enabled_entities(self, config: InputGuardConfig) -> list[PIIType]:
        types: list[PIIType] = []
        for name in config.detect_entities:
            pii_type = _entity_name_to_type(name)
            if pii_type is not None:
                types.append(pii_type)
        return types or list(PIIType)

    @staticmethod
    def _action_for(scanner_action: ScannerAction) -> str:
        if scanner_action == ScannerAction.BLOCK:
            return "blocked"
        if scanner_action == ScannerAction.FLAG:
            return "flagged"
        if scanner_action == ScannerAction.REDACT:
            return "redacted"
        return "blocked"
