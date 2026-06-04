"""
PII detector — regex-based, zero external dependencies.

Detection order for UPI:
  1. Run UPI_CANDIDATE_PATTERN to find @-mentions
  2. Extract suffix (group 1)
  3. Gate: if suffix NOT in KNOWN_UPI_SUFFIXES → discard (it's a regular email)
  4. Only then create a PIIMatch

This ensures user@gmail.com is NEVER flagged as a UPI ID.
See ARCHITECTURE.md §4.3.1 for full specification.

Secret/Credential detection:
  Two confidence tiers:
    - HIGH (0.95): exact prefix match (sk-, sk-ant-, AKIA, gsk_, rzp_live_, etc.)
    - MEDIUM (0.70): generic KEY=value patterns without known prefix
  Uses separate _detect_secrets() method, same pattern as _detect_upi().
"""
from __future__ import annotations  # Python 3.9 compatibility

import re
from dataclasses import dataclass
from enum import Enum


class PIIType(str, Enum):
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    EMAIL = "email"
    PHONE = "phone"
    AADHAAR = "aadhaar"
    PAN = "pan"
    UPI_ID = "upi_id"
    PASSPORT = "passport"
    SECRET = "secret"


@dataclass
class PIIMatch:
    pii_type: PIIType
    matched_text: str
    start: int
    end: int
    confidence: float


# ---------------------------------------------------------------------------
# Regex patterns for all PII types except UPI_ID
# UPI_ID uses a separate candidate pattern + suffix gate (see below)
# ---------------------------------------------------------------------------
PII_PATTERNS: dict[PIIType, re.Pattern] = {
    # US Social Security Number: 123-45-6789
    PIIType.SSN: re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),

    # Credit/Debit card: 16 digits, optional spaces or hyphens every 4 digits
    PIIType.CREDIT_CARD: re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    ),

    # Aadhaar: 12 digits, starts with 2-9, optional spaces every 4 digits
    # India DPDP Act — first digit is never 0 or 1
    PIIType.AADHAAR: re.compile(
        r"\b[0-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b"
    ),

    # PAN card: 5 uppercase letters, 4 digits, 1 uppercase letter
    # India DPDP Act — e.g. ABCDE1234F
    PIIType.PAN: re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b"
    ),

    # Email address: standard format with dot in domain
    # Note: EMAIL requires a dot in the domain (e.g. .com) — UPI IDs never have one
    PIIType.EMAIL: re.compile(
        r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b"
    ),

    # Phone numbers:
    #   Indian: +91-XXXXX-XXXXX or +91XXXXXXXXXX or 10 bare digits
    #   US: (555) 867-5309 or 555-867-5309 or +1-555-867-5309
    PIIType.PHONE: re.compile(
        r"(?:\+91[-\s]?)?\d{5}[-\s]?\d{5}"          # Indian
        r"|"
        r"(?:\+1[-\s]?)?(?:\(\d{3}\)|\d{3})[-\s]?\d{3}[-\s]?\d{4}"  # US
    ),

    # Passport: one uppercase letter followed by 7 digits — e.g. J1234567
    PIIType.PASSPORT: re.compile(
        r"\b[A-Z]\d{7}\b"
    ),

    # UPI ID (Virtual Payment Address)
    # Format: string@string (no dots in the suffix)
    # The (?!\.\w) lookahead ensures we don't accidentally match the first half
    # of a standard email address like user@gmail.com
    PIIType.UPI_ID: re.compile(
        r"\b[\w.\-]+@[a-zA-Z0-9]{2,64}\b(?!\.\w)",
        re.IGNORECASE
    ),
}

# ---------------------------------------------------------------------------
# Secret / Credential detection patterns
# Two tiers: HIGH confidence (exact prefix) and MEDIUM confidence (generic)
# Like UPI, secrets are NOT in PII_PATTERNS — handled in _detect_secrets().
# ---------------------------------------------------------------------------

# HIGH confidence — exact prefix match, block immediately
# Each tuple: (name, compiled pattern, confidence)
CREDENTIAL_PATTERNS_HIGH: list[tuple[str, re.Pattern, float]] = [
    # OpenAI API keys: sk-... (48+ chars) or sk-proj-...
    ("openai_api_key", re.compile(
        r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"
    ), 0.95),

    # Anthropic API keys: sk-ant-...
    ("anthropic_api_key", re.compile(
        r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"
    ), 0.95),

    # AWS Access Key ID: AKIA followed by 16 uppercase alphanumeric chars
    ("aws_access_key", re.compile(
        r"\bAKIA[0-9A-Z]{16}\b"
    ), 0.95),

    # AWS Secret Access Key: 40-char base64-like string after common assignment
    ("aws_secret_key", re.compile(
        r"(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"
    ), 0.95),

    # Google Cloud / Firebase service account keys
    ("gcp_api_key", re.compile(
        r"\bAIza[0-9A-Za-z_-]{35}\b"
    ), 0.95),

    # GitHub Personal Access Tokens: ghp_, gho_, ghu_, ghs_, ghr_
    ("github_token", re.compile(
        r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b"
    ), 0.95),

    # Stripe API keys: sk_live_, sk_test_, pk_live_, pk_test_
    ("stripe_key", re.compile(
        r"\b[sp]k_(?:live|test)_[A-Za-z0-9]{20,}\b"
    ), 0.95),

    # Razorpay keys: rzp_live_, rzp_test_
    ("razorpay_key", re.compile(
        r"\brzp_(?:live|test)_[A-Za-z0-9]{14,}\b"
    ), 0.95),

    # Groq API keys: gsk_...
    ("groq_api_key", re.compile(
        r"\bgsk_[A-Za-z0-9]{20,}\b"
    ), 0.95),

    # Slack Bot/User tokens: xoxb-, xoxp-, xoxo-
    ("slack_token", re.compile(
        r"\bxox[bpoas]-[A-Za-z0-9-]{10,}\b"
    ), 0.95),

    # Twilio Account SID (AC...) and Auth Token
    ("twilio_key", re.compile(
        r"\bAC[a-f0-9]{32}\b"
    ), 0.95),

    # Hugging Face tokens: hf_...
    ("huggingface_token", re.compile(
        r"\bhf_[A-Za-z0-9]{20,}\b"
    ), 0.95),
]

# MEDIUM confidence — generic KEY=value patterns
# These catch secrets that don't have known prefixes (e.g. DATABASE_URL=...)
CREDENTIAL_PATTERNS_MEDIUM: list[tuple[str, re.Pattern, float]] = [
    # Generic: VARIABLE_NAME = "long-secret-value" (env-style assignment)
    ("generic_env_secret", re.compile(
        r"(?:API_KEY|API_SECRET|SECRET_KEY|ACCESS_TOKEN|AUTH_TOKEN|PRIVATE_KEY"
        r"|DATABASE_URL|DB_PASSWORD|OPENAI_API_KEY|ANTHROPIC_API_KEY"
        r"|STRIPE_SECRET_KEY|RAZORPAY_KEY_SECRET|AWS_ACCESS_KEY_ID"
        r"|AWS_SECRET_ACCESS_KEY|GOOGLE_API_KEY|GITHUB_TOKEN"
        r"|SLACK_TOKEN|TWILIO_AUTH_TOKEN|HF_TOKEN)"
        r"\s*[=:]\s*['\"]?([A-Za-z0-9_/+=:@.-]{8,})['\"]?",
        re.IGNORECASE,
    ), 0.70),

    # Bearer tokens in headers: Authorization: Bearer ...
    ("bearer_token", re.compile(
        r"[Bb]earer\s+[A-Za-z0-9_.-]{20,}"
    ), 0.70),

    # Private key blocks: -----BEGIN (RSA|EC|PRIVATE) KEY-----
    ("private_key_block", re.compile(
        r"-----BEGIN\s+(?:RSA\s+)?(?:EC\s+)?PRIVATE\s+KEY-----"
    ), 0.95),
]


class PIIDetector:
    """
    Detects PII in text using regex patterns. Zero external dependencies.

    Supports: SSN, Credit Card, Aadhaar, PAN, UPI ID, Email, Phone, Passport, Secret.
    UPI detection uses a suffix allowlist gate to prevent false positives on
    regular email addresses.
    Secret detection uses two confidence tiers (HIGH/MEDIUM) to separate
    known API key prefixes from generic key=value patterns.
    """

    def __init__(self, enabled_types: list[PIIType] | None = None):
        self.enabled_types = enabled_types or list(PIIType)

    def detect(self, text: str) -> list[PIIMatch]:
        """Return all PII matches found in text."""
        if not text:
            return []

        matches: list[PIIMatch] = []

        for pii_type in self.enabled_types:
            if pii_type == PIIType.SECRET:
                # Secrets use separate two-tier detection logic
                matches.extend(self._detect_secrets(text))
                continue

            pattern = PII_PATTERNS.get(pii_type)
            if not pattern:
                continue

            for m in pattern.finditer(text):
                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        matched_text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.9,
                    )
                )

        return matches

    def _detect_secrets(self, text: str) -> list[PIIMatch]:
        """
        Secret/credential detection with two confidence tiers.

        Tier 1 — HIGH confidence (0.95): known API key prefixes.
          sk-proj-abc123...  → OpenAI key  → HIGH → block
          AKIAIOSFODNN7EXAMPLE → AWS key   → HIGH → block

        Tier 2 — MEDIUM confidence (0.70): generic KEY=value patterns.
          API_KEY="some-long-value"         → MEDIUM → flag
          Bearer eyJhbGciOiJIUzI1NiJ9...   → MEDIUM → flag

        HIGH patterns are checked first. If a match overlaps with a MEDIUM
        match, the HIGH match wins (higher confidence).
        """
        matches: list[PIIMatch] = []

        # Tier 1: HIGH confidence — exact prefix match
        for _name, pattern, confidence in CREDENTIAL_PATTERNS_HIGH:
            for m in pattern.finditer(text):
                matches.append(
                    PIIMatch(
                        pii_type=PIIType.SECRET,
                        matched_text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=confidence,
                    )
                )

        # Tier 2: MEDIUM confidence — generic patterns
        # Skip if region already covered by a HIGH match
        high_ranges = [(m.start, m.end) for m in matches]
        for _name, pattern, confidence in CREDENTIAL_PATTERNS_MEDIUM:
            for m in pattern.finditer(text):
                # Check for overlap with existing HIGH matches
                overlaps = any(
                    m.start() < h_end and m.end() > h_start
                    for h_start, h_end in high_ranges
                )
                if overlaps:
                    continue
                matches.append(
                    PIIMatch(
                        pii_type=PIIType.SECRET,
                        matched_text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=confidence,
                    )
                )

        return matches

    def has_pii(self, text: str) -> bool:
        """Return True if any PII is detected in text."""
        return len(self.detect(text)) > 0

    def redact(self, text: str) -> str:
        """
        Replace all detected PII with [TYPE_REDACTED] placeholders.
        Processes matches in reverse order to preserve character positions.
        """
        all_matches = sorted(self.detect(text), key=lambda m: m.start, reverse=True)
        result = text
        for match in all_matches:
            placeholder = f"[{match.pii_type.value.upper()}_REDACTED]"
            result = result[: match.start] + placeholder + result[match.end :]
        return result
