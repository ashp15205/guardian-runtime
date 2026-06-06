"""YAML policy loader and Pydantic schema validation.

Reads a guardian_runtime_policy.yaml file, validates it against a strict Pydantic V2
schema, and returns a Policy object that every GuardianRuntime component uses.

If the YAML has typos, missing fields, or wrong types, Pydantic will raise a
clear PolicyValidationError with details.

See ARCHITECTURE.md §4.7 for full specification.
"""
from __future__ import annotations  # Python 3.9 compatibility

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums for strict validation
# ---------------------------------------------------------------------------

class ScannerAction(str, Enum):
    """The action to take when the scanner detects a violation."""
    BLOCK = "block"
    REDACT = "redact"
    FLAG = "flag"


class LogSink(str, Enum):
    """Where to write GuardianRuntime logs."""
    JSONL = "jsonl"
    CONSOLE = "console"
    BOTH = "both"


class LogLevel(str, Enum):
    """What severity of events to log."""
    ALL = "ALL"
    VIOLATIONS_ONLY = "VIOLATIONS_ONLY"
    HIGH_SEVERITY = "HIGH_SEVERITY"





class LLMProvider(str, Enum):
    """Runtime LLM provider for GuardianRuntime.complete()."""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


class InteractiveMode(str, Enum):
    """Interactive terminal mode when violations are found.

    - off        : Silent block / follow scanner_action (default, safe for production).
    - warn_ask   : Print a detailed warning and ask the developer [y/N] whether
                   to proceed.  Only suitable for local development / CLI tools.
    """
    OFF = "off"
    WARN_ASK = "warn_ask"


class LLMConfig(BaseModel):
    """Per-agent LLM provider settings."""
    provider: LLMProvider = LLMProvider.OPENAI
    default_model: Optional[str] = None


class LoopAction(str, Enum):
    """Action to take when a prompt loop is detected."""
    BLOCK = "block"
    BLOCK_AND_ALERT = "block_and_alert"


# Valid PII entity names — must match PIIType enum values in pii.py
VALID_PII_ENTITIES = frozenset({
    "ssn", "credit_card", "email", "phone",
    "aadhaar", "pan", "upi_id", "passport", "secret",
})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PolicyValidationError(Exception):
    """Raised when a YAML policy file fails schema validation.

    Attributes:
        errors: List of Pydantic validation error dicts.
    """

    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.errors = errors or []


# ---------------------------------------------------------------------------
# Config sub-models
# ---------------------------------------------------------------------------

class ScopeConfig(BaseModel):
    """Topic-scoping configuration for the Input Guard."""
    allowed_topics: List[str] = Field(default_factory=list)
    block_message: str = "This topic is outside my scope."


class InputGuardConfig(BaseModel):
    """Configuration for the Input Guard pipeline."""
    scanner_enabled: bool = True
    detect_entities: List[str] = Field(
        default_factory=lambda: ["secret"],
        description="List of entities to detect. Defaults to secrets only for developer workflows.",
    )
    scanner_action: ScannerAction = ScannerAction.BLOCK
    jailbreak_detection: bool = True
    scope: Optional[ScopeConfig] = None

    @field_validator("detect_entities")
    @classmethod
    def validate_detect_entities(cls, v: List[str]) -> List[str]:
        """Ensure every entity name matches a known PIIType value."""
        invalid = [e for e in v if e not in VALID_PII_ENTITIES]
        if invalid:
            raise ValueError(
                f"Unknown scanner entities: {invalid}. "
                f"Valid values: {sorted(VALID_PII_ENTITIES)}"
            )
        return v


class OutputGuardConfig(BaseModel):
    """Configuration for the Output Guard pipeline."""
    scanner_enabled: bool = True
    profanity_filter: bool = False
    competitor_block: List[str] = Field(default_factory=list)


class AutoDowngradeConfig(BaseModel):
    """Auto-downgrade model when budget threshold is reached."""
    enabled: bool = False
    threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    target_model: str = "gpt-3.5-turbo"


class LoopConfig(BaseModel):
    """Semantic loop detection settings."""
    max_retries: int = Field(default=3, ge=1)
    similarity_threshold: float = Field(default=0.90, ge=0.0, le=1.0)
    action: LoopAction = LoopAction.BLOCK_AND_ALERT


class CostConfig(BaseModel):
    """FinOps budget and cost control settings."""
    daily_budget: float = Field(default=10.00, ge=0.0)
    monthly_budget: Optional[float] = Field(default=None, ge=0.0)
    per_session_limit: float = Field(default=0.50, ge=0.0)
    max_input_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Block LLM call when input exceeds this token count.",
    )
    currency: str = "USD"
    auto_downgrade: Optional[AutoDowngradeConfig] = None
    loop_detection: Optional[LoopConfig] = None


class RateLimitConfig(BaseModel):
    """Rate limit for a specific tool."""
    max_calls: int = Field(ge=1)
    per: str = "session"  # "session" | "minute" | "hour"
    cooldown_seconds: int = Field(default=0, ge=0)


class ArgRuleConfig(BaseModel):
    """Argument validation rule for a tool parameter."""
    type: str = "string"  # "string" | "int" | "enum"
    pattern: Optional[str] = None
    values: Optional[List[str]] = None


class ToolConfig(BaseModel):
    """Tool governance configuration."""
    allowed: List[str] = Field(default_factory=list)
    denied: List[str] = Field(default_factory=list)
    rate_limits: Dict[str, RateLimitConfig] = Field(default_factory=dict)
    argument_validation: Dict[str, Dict[str, ArgRuleConfig]] = Field(
        default_factory=dict
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    sink: LogSink = LogSink.JSONL
    log_level: LogLevel = LogLevel.ALL
    retention_days: int = Field(default=30, ge=1)


class AlertConfig(BaseModel):
    """Alert/notification configuration (v0.2+)."""
    slack_webhook: Optional[str] = None
    email: Optional[str] = None


class ComplianceConfig(BaseModel):
    """Compliance framework configuration."""
    frameworks: List[str] = Field(default_factory=list)  # e.g. ["dpdp", "gdpr"]


class OptimizerConfig(BaseModel):
    """Input optimization settings."""
    enabled: bool = True
    whitespace_normalization: bool = True
    max_history_messages: Optional[int] = Field(
        default=None, ge=1,
        description="Keep only the last N user/assistant turns. System prompt always kept."
    )
    deduplicate_system_prompts: bool = True
    remove_empty_messages: bool = True
    document_conversion: bool = True  # auto-convert if markitdown installed
    warn_at_token_pct: float = Field(
        default=0.80, ge=0.0, le=1.0,
        description="Warn when input tokens reach this % of max_input_tokens"
    )
    terse_mode: bool = Field(
        default=False,
        description="Injects a system prompt forcing the LLM to output extreme shorthand, drastically reducing output tokens while maintaining accuracy."
    )



# ---------------------------------------------------------------------------
# Agent-level policy
# ---------------------------------------------------------------------------

class AgentPolicy(BaseModel):
    """Complete policy for a single agent."""
    llm: Optional[LLMConfig] = None
    input_guard: Optional[InputGuardConfig] = Field(default_factory=InputGuardConfig)
    output_guard: Optional[OutputGuardConfig] = None
    cost: Optional[CostConfig] = Field(default_factory=CostConfig)
    tools: Optional[ToolConfig] = None
    optimizer: Optional[OptimizerConfig] = Field(default_factory=OptimizerConfig)


# ---------------------------------------------------------------------------
# Root Policy model
# ---------------------------------------------------------------------------

class Policy(BaseModel):
    """Root policy model — represents a complete guardian_runtime_policy.yaml file.

    Usage:
        policy = load_policy("guardian_runtime_policy.yaml")
        agent_config = policy.get_agent("support-bot")
    """
    version: str = "1.0"
    name: str = "default"
    environment: Optional[str] = None  # "dev" | "staging" | "production"
    interactive_mode: InteractiveMode = InteractiveMode.OFF
    agents: Dict[str, AgentPolicy] = Field(default_factory=dict)
    logging: Optional[LoggingConfig] = None
    alerts: Optional[AlertConfig] = None
    compliance: Optional[ComplianceConfig] = None

    @model_validator(mode="after")
    def ensure_default_agent(self) -> "Policy":
        """Ensure there is at least a 'default' agent entry."""
        if not self.agents:
            self.agents = {"default": AgentPolicy()}
        return self

    def get_agent(self, agent_id: str) -> AgentPolicy:
        """Get configuration for a specific agent, falling back to 'default'.

        Args:
            agent_id: The agent identifier to look up.

        Returns:
            AgentPolicy for the given agent, or the 'default' agent if not found.
        """
        if agent_id in self.agents:
            return self.agents[agent_id]
        return self.agents.get("default", AgentPolicy())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_policy(path: str | Path) -> Policy:
    """Load and validate a GuardianRuntime YAML policy file.

    Args:
        path: Path to the YAML policy file.

    Returns:
        A fully validated Policy object.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        PolicyValidationError: If the YAML content fails schema validation.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise PolicyValidationError(
            f"Policy file is empty: {path}"
        )

    if not isinstance(raw, dict):
        raise PolicyValidationError(
            f"Policy file must contain a YAML mapping, got {type(raw).__name__}: {path}"
        )

    try:
        return Policy.model_validate(raw)
    except Exception as e:
        # Re-wrap Pydantic ValidationError into our own exception
        errors = []
        if hasattr(e, "errors"):
            errors = e.errors()  # type: ignore[union-attr]
        raise PolicyValidationError(
            f"Policy validation failed for {path}: {e}",
            errors=errors,
        ) from e
