"""Tests for the Policy Engine (guardian/core/policy.py).

Covers:
  - Loading a valid YAML file and checking defaults
  - Strict pii_entities validation
  - Agent fallback via get_agent()
  - Invalid YAML handling (missing fields, wrong types, unknown entities)
  - OutputGuard BYOM hallucination_provider validation
  - CostConfig bounds validation
  - Empty and malformed files
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from guardian.core.policy import (
    AgentPolicy,
    AutoDowngradeConfig,
    CostConfig,
    HallucinationProvider,
    InputGuardConfig,
    LoggingConfig,
    LogSink,
    LoopAction,
    LoopConfig,
    OutputGuardConfig,
    PIIAction,
    Policy,
    PolicyValidationError,
    ScopeConfig,
    load_policy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_yaml(tmp_path: Path) -> Path:
    """Create a minimal valid policy YAML file."""
    policy_file = tmp_path / "minimal.yaml"
    policy_file.write_text(textwrap.dedent("""\
        version: "1.0"
        name: "test-minimal"
        agents:
          default:
            input_guard:
              pii_detection: true
              pii_entities: [aadhaar, pan, upi_id, credit_card, ssn, email, phone, secret]
              jailbreak_detection: true
            output_guard:
              hallucination_check: false
              hallucination_provider: openai
              hallucination_model: gpt-4o-mini
              pii_detection: true
            cost:
              per_session_limit: 1.00
    """))
    return policy_file


@pytest.fixture
def full_yaml(tmp_path: Path) -> Path:
    """Create a fully-featured policy YAML file."""
    policy_file = tmp_path / "full.yaml"
    policy_file.write_text(textwrap.dedent("""\
        version: "1.0"
        name: "production"
        environment: "production"
        agents:
          default:
            input_guard:
              pii_detection: true
              pii_entities: [aadhaar, pan, ssn, secret]
              pii_action: block
              jailbreak_detection: true
              scope:
                allowed_topics: ["billing", "product", "support"]
                block_message: "I can only help with billing, product, and support."
            output_guard:
              hallucination_check: true
              hallucination_provider: ollama
              hallucination_model: llama3
              pii_detection: true
              profanity_filter: true
              competitor_block: ["CompetitorA", "CompetitorB"]
            cost:
              daily_budget: 10.00
              monthly_budget: 200.00
              per_session_limit: 0.50
              currency: USD
              auto_downgrade:
                enabled: true
                threshold: 0.80
                target_model: gpt-3.5-turbo
              loop_detection:
                max_retries: 3
                similarity_threshold: 0.90
                action: block_and_alert
          support-bot:
            input_guard:
              pii_detection: true
              pii_entities: [aadhaar, pan]
              jailbreak_detection: false
        logging:
          sink: jsonl
          log_level: VIOLATIONS_ONLY
          retention_days: 90
    """))
    return policy_file


# ---------------------------------------------------------------------------
# Test: Loading valid YAML files
# ---------------------------------------------------------------------------

class TestLoadValidPolicy:
    """Test loading valid YAML policy files."""

    def test_load_minimal(self, minimal_yaml: Path):
        policy = load_policy(minimal_yaml)
        assert policy.version == "1.0"
        assert policy.name == "test-minimal"
        assert "default" in policy.agents

    def test_minimal_input_guard(self, minimal_yaml: Path):
        policy = load_policy(minimal_yaml)
        ig = policy.agents["default"].input_guard
        assert ig is not None
        assert ig.pii_detection is True
        assert ig.jailbreak_detection is True
        assert "aadhaar" in ig.pii_entities
        assert "secret" in ig.pii_entities

    def test_minimal_output_guard(self, minimal_yaml: Path):
        policy = load_policy(minimal_yaml)
        og = policy.agents["default"].output_guard
        assert og is not None
        assert og.hallucination_check is False
        assert og.hallucination_provider == HallucinationProvider.OPENAI
        assert og.hallucination_model == "gpt-4o-mini"

    def test_minimal_cost(self, minimal_yaml: Path):
        policy = load_policy(minimal_yaml)
        cost = policy.agents["default"].cost
        assert cost is not None
        assert cost.per_session_limit == 1.00

    def test_load_full(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        assert policy.environment == "production"
        assert "default" in policy.agents
        assert "support-bot" in policy.agents

    def test_full_scope(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        scope = policy.agents["default"].input_guard.scope
        assert scope is not None
        assert "billing" in scope.allowed_topics
        assert scope.block_message == "I can only help with billing, product, and support."

    def test_full_output_guard_byom(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        og = policy.agents["default"].output_guard
        assert og.hallucination_check is True
        assert og.hallucination_provider == HallucinationProvider.OLLAMA
        assert og.hallucination_model == "llama3"
        assert og.profanity_filter is True
        assert og.competitor_block == ["CompetitorA", "CompetitorB"]

    def test_full_cost_config(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        cost = policy.agents["default"].cost
        assert cost.daily_budget == 10.00
        assert cost.monthly_budget == 200.00
        assert cost.auto_downgrade is not None
        assert cost.auto_downgrade.enabled is True
        assert cost.auto_downgrade.threshold == 0.80
        assert cost.auto_downgrade.target_model == "gpt-3.5-turbo"

    def test_full_loop_detection(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        loop = policy.agents["default"].cost.loop_detection
        assert loop is not None
        assert loop.max_retries == 3
        assert loop.similarity_threshold == 0.90
        assert loop.action == LoopAction.BLOCK_AND_ALERT

    def test_full_logging(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        assert policy.logging is not None
        assert policy.logging.sink == LogSink.JSONL
        assert policy.logging.log_level.value == "VIOLATIONS_ONLY"
        assert policy.logging.retention_days == 90


# ---------------------------------------------------------------------------
# Test: Agent fallback
# ---------------------------------------------------------------------------

class TestGetAgent:
    """Test get_agent() fallback behavior."""

    def test_returns_specific_agent(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        agent = policy.get_agent("support-bot")
        assert agent.input_guard is not None
        assert agent.input_guard.pii_entities == ["aadhaar", "pan"]
        assert agent.input_guard.jailbreak_detection is False

    def test_falls_back_to_default(self, full_yaml: Path):
        policy = load_policy(full_yaml)
        agent = policy.get_agent("unknown-agent-xyz")
        # Should return the "default" agent
        assert agent.input_guard is not None
        assert "secret" in agent.input_guard.pii_entities

    def test_empty_agents_creates_default(self):
        policy = Policy(version="1.0", name="empty")
        agent = policy.get_agent("anything")
        assert isinstance(agent, AgentPolicy)


# ---------------------------------------------------------------------------
# Test: PII entity validation
# ---------------------------------------------------------------------------

class TestPIIEntityValidation:
    """Test that pii_entities are validated against the known set."""

    def test_valid_entities_accepted(self):
        config = InputGuardConfig(
            pii_entities=["aadhaar", "pan", "ssn", "secret"]
        )
        assert config.pii_entities == ["aadhaar", "pan", "ssn", "secret"]

    def test_invalid_entity_rejected(self):
        with pytest.raises(Exception, match="Unknown PII entities"):
            InputGuardConfig(pii_entities=["aadhaar", "invalid_entity"])

    def test_all_valid_entities_accepted(self):
        all_entities = ["ssn", "credit_card", "email", "phone",
                        "aadhaar", "pan", "upi_id", "passport", "secret"]
        config = InputGuardConfig(pii_entities=all_entities)
        assert len(config.pii_entities) == 9


# ---------------------------------------------------------------------------
# Test: Hallucination provider validation (BYOM)
# ---------------------------------------------------------------------------

class TestBYOMProvider:
    """Test Bring Your Own Model provider enum validation."""

    @pytest.mark.parametrize("provider", ["openai", "anthropic", "ollama", "gemini"])
    def test_valid_providers_accepted(self, provider: str):
        config = OutputGuardConfig(hallucination_provider=provider)
        assert config.hallucination_provider.value == provider

    def test_invalid_provider_rejected(self):
        with pytest.raises(Exception):
            OutputGuardConfig(hallucination_provider="invalid_provider")

    def test_default_provider_is_openai(self):
        config = OutputGuardConfig()
        assert config.hallucination_provider == HallucinationProvider.OPENAI
        assert config.hallucination_model == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Test: Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Test that bad YAML files produce clear errors."""

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match="Policy file not found"):
            load_policy(tmp_path / "nonexistent.yaml")

    def test_empty_file(self, tmp_path: Path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        with pytest.raises(PolicyValidationError, match="empty"):
            load_policy(empty)

    def test_non_mapping_file(self, tmp_path: Path):
        bad = tmp_path / "list.yaml"
        bad.write_text("- item1\n- item2\n")
        with pytest.raises(PolicyValidationError, match="mapping"):
            load_policy(bad)

    def test_invalid_pii_entity_in_yaml(self, tmp_path: Path):
        bad = tmp_path / "bad_entity.yaml"
        bad.write_text(textwrap.dedent("""\
            version: "1.0"
            name: "bad"
            agents:
              default:
                input_guard:
                  pii_entities: [aadhaar, totally_fake_type]
        """))
        with pytest.raises(PolicyValidationError):
            load_policy(bad)

    def test_invalid_cost_budget_negative(self, tmp_path: Path):
        bad = tmp_path / "bad_cost.yaml"
        bad.write_text(textwrap.dedent("""\
            version: "1.0"
            name: "bad"
            agents:
              default:
                cost:
                  daily_budget: -5.00
        """))
        with pytest.raises(PolicyValidationError):
            load_policy(bad)


# ---------------------------------------------------------------------------
# Test: Loading the real minimal.yaml from the project
# ---------------------------------------------------------------------------

class TestRealPolicyFile:
    """Test loading the actual policies/minimal.yaml from the project."""

    def test_load_real_minimal_yaml(self):
        real_path = Path(__file__).parent.parent.parent / "policies" / "minimal.yaml"
        if not real_path.exists():
            pytest.skip("policies/minimal.yaml not found")
        policy = load_policy(real_path)
        assert policy.name == "minimal"
        assert "default" in policy.agents
        ig = policy.agents["default"].input_guard
        assert ig is not None
        assert "secret" in ig.pii_entities
