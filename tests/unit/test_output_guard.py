"""Tests for OutputGuard."""

from guardian.core.policy import AgentPolicy, OutputGuardConfig
from guardian.guards.output_guard import OutputGuard


def test_blocks_pii_in_output():
    guard = OutputGuard()
    policy = AgentPolicy(output_guard=OutputGuardConfig(pii_detection=True))
    result = guard.check("Your SSN is 123-45-6789", policy)
    assert result.allowed is False
    assert any(v.type == "output_pii" for v in result.violations)


def test_allows_clean_output():
    guard = OutputGuard()
    policy = AgentPolicy(output_guard=OutputGuardConfig(pii_detection=True))
    result = guard.check("Paris is the capital of France.", policy)
    assert result.allowed is True
