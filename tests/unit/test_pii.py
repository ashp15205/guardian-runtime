"""
Tests for PIIDetector.

Run with: pytest tests/unit/test_pii.py -v

These tests will FAIL until guardian/guards/validators/pii.py is implemented.
That is expected. This file is your test-first spec for Week 3.
"""

import pytest
from guardian.guards.validators.pii import PIIDetector, PIIType


@pytest.fixture
def detector():
    return PIIDetector()


# ──────────────────────────────────────────────
# Detection tests — these must all find a match
# ──────────────────────────────────────────────

@pytest.mark.parametrize("text,expected_type", [
    ("My SSN is 123-45-6789",                  PIIType.SSN),
    ("Card number: 4111 1111 1111 1111",        PIIType.CREDIT_CARD),
    ("Aadhaar: 0000 0000 0000",                 PIIType.AADHAAR),
    ("PAN card: ABCDE1234F",                    PIIType.PAN),
    ("Pay me at username@ybl",                  PIIType.UPI_ID),
    ("UPI: name@paytm",                         PIIType.UPI_ID),
    ("UPI: handle@oksbi",                       PIIType.UPI_ID),
    ("Email: test@example.com",                 PIIType.EMAIL),
    ("Phone: +91-98765-43210",                  PIIType.PHONE),
    ("US Phone: (555) 867-5309",                PIIType.PHONE),
    ("Passport: J1234567",                      PIIType.PASSPORT),
    # Secret / Credential detection
    ("My key is sk-proj-abc123def456ghi789jkl012",      PIIType.SECRET),
    ("Use AKIAIOSFODNN7EXAMPLE for AWS",                PIIType.SECRET),
    ("Token: ghp_ABCDEFghijklmnop1234567890abcdefghijkl", PIIType.SECRET),
    ("Stripe: sk" + "_live_51J4abc123def456ghi789jkl",       PIIType.SECRET),
    ("Razorpay: rzp_live_abcdef12345678",               PIIType.SECRET),
    ("Groq: gsk_abc123def456ghi789jkl012mno",           PIIType.SECRET),
    ("Slack: xoxb-123-456-abcdefghij",                  PIIType.SECRET),
    ("HF token: hf_abcdef123456ghijklmnopqr",           PIIType.SECRET),
])
def test_detects_pii(detector, text, expected_type):
    matches = detector.detect(text)
    assert len(matches) > 0, f"Expected to detect {expected_type} in: {text!r}"
    assert any(m.pii_type == expected_type for m in matches), (
        f"Expected {expected_type} but got {[m.pii_type for m in matches]}"
    )


# ──────────────────────────────────────────────────────────────
# False positive tests — these must NOT trigger PII detection
# ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,should_not_flag", [
    # CRITICAL: email addresses must not be flagged as UPI IDs
    ("Send to admin@gmail.com",         PIIType.UPI_ID),
    ("Contact: user@outlook.com",       PIIType.UPI_ID),
    ("Email: support@company.co.in",    PIIType.UPI_ID),
    ("Reach me at hello@yahoo.com",     PIIType.UPI_ID),
    # Normal numbers must not be flagged as Aadhaar
    ("Project ID: 12345678",            PIIType.AADHAAR),
    ("Order #: 9876543210",             PIIType.AADHAAR),
    # Normal strings must not be flagged as secrets
    ("The sky is blue",                 PIIType.SECRET),
    ("Use version 2.0 of the SDK",     PIIType.SECRET),
    ("sk is short for skill",          PIIType.SECRET),
])
def test_no_false_positives(detector, text, should_not_flag):
    matches = detector.detect(text)
    flagged_types = [m.pii_type for m in matches]
    assert should_not_flag not in flagged_types, (
        f"False positive: {should_not_flag} incorrectly flagged in: {text!r}"
    )


def test_clean_text_has_no_pii(detector):
    clean = "What is the capital of France?"
    assert detector.has_pii(clean) is False


def test_empty_string(detector):
    assert detector.detect("") == []


# ────────────────────────────────
# Redaction tests
# ────────────────────────────────

def test_redact_removes_aadhaar(detector):
    text = "My Aadhaar is 0000 0000 0000"
    redacted = detector.redact(text)
    assert "0000 0000 0000" not in redacted
    assert "[AADHAAR_REDACTED]" in redacted


def test_redact_removes_pan(detector):
    text = "PAN: ABCDE1234F"
    redacted = detector.redact(text)
    assert "ABCDE1234F" not in redacted
    assert "[PAN_REDACTED]" in redacted


def test_redact_multiple_pii_types(detector):
    text = "SSN: 123-45-6789 and Aadhaar: 0000 0000 0000"
    redacted = detector.redact(text)
    assert "123-45-6789" not in redacted
    assert "0000 0000 0000" not in redacted


# ────────────────────────────────────
# UPI suffix gate — the critical test
# ────────────────────────────────────

class TestUPISuffixGate:
    """These tests exist specifically to verify the suffix gate runs BEFORE flagging."""

    VALID_UPI = [
        "username@ybl",
        "name@paytm",
        "handle@oksbi",
        "user@okaxis",
        "test@okhdfcbank",
        "person@upi",
        "buyer@apl",
        "seller@ibl",
    ]

    INVALID_UPI = [
        "user@gmail.com",
        "admin@outlook.com",
        "support@company.com",
        "user@yahoo.co.in",
        "contact@hotmail.com",
    ]

    def test_valid_upi_ids_detected(self, detector):
        for upi in self.VALID_UPI:
            matches = detector.detect(upi)
            assert any(m.pii_type == PIIType.UPI_ID for m in matches), (
                f"Valid UPI ID not detected: {upi!r}"
            )

    def test_emails_not_flagged_as_upi(self, detector):
        for email in self.INVALID_UPI:
            matches = detector.detect(email)
            upi_matches = [m for m in matches if m.pii_type == PIIType.UPI_ID]
            assert len(upi_matches) == 0, (
                f"Email incorrectly flagged as UPI: {email!r}"
            )


# ────────────────────────────────────────────────
# Secret / Credential detection tests
# ────────────────────────────────────────────────

class TestSecretDetection:
    """Tests for SECRET PIIType — API keys and credentials."""

    # HIGH confidence — exact prefix match
    HIGH_CONFIDENCE_SECRETS = [
        "sk-proj-abc123def456ghi789jkl012mno345",            # OpenAI
        "sk-ant-api03-abcdef123456ghijklmnopqr",             # Anthropic
        "AKIAIOSFODNN7EXAMPLE",                               # AWS
        "ghp_ABCDEFghijklmnop1234567890abcdefghijkl",        # GitHub
        "sk" + "_live_51J4abcdef123456ghijklmnop",                 # Stripe
        "rzp_live_abcdef12345678",                            # Razorpay
        "gsk_abc123def456ghi789jkl012mno",                   # Groq
        "xoxb-123-456-abcdefghij",                            # Slack
        "hf_abcdef123456ghijklmnopqr",                       # Hugging Face
    ]

    # MEDIUM confidence — generic patterns
    MEDIUM_CONFIDENCE_SECRETS = [
        'OPENAI_API_KEY="sk-some-long-fake-key-value-here"',
        'API_KEY=abcdef123456ghijklmn',
        'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
        '-----BEGIN PRIVATE KEY-----',
    ]

    # False positives — should NOT be flagged as secrets
    NOT_SECRETS = [
        "The project costs $500 and ships in 3 weeks",
        "Use the sklearn library for ML",
        "sk is short for skill in gaming",
        "I like skiing in the Alps",
        "The temperature is 95 degrees",
    ]

    def test_high_confidence_secrets_detected(self, detector):
        for secret in self.HIGH_CONFIDENCE_SECRETS:
            text = f"Here is a key: {secret}"
            matches = detector.detect(text)
            secret_matches = [m for m in matches if m.pii_type == PIIType.SECRET]
            assert len(secret_matches) > 0, (
                f"HIGH confidence secret not detected: {secret!r}"
            )
            assert secret_matches[0].confidence == 0.95, (
                f"Expected HIGH confidence (0.95) for: {secret!r}"
            )

    def test_medium_confidence_secrets_detected(self, detector):
        for secret in self.MEDIUM_CONFIDENCE_SECRETS:
            matches = detector.detect(secret)
            secret_matches = [m for m in matches if m.pii_type == PIIType.SECRET]
            assert len(secret_matches) > 0, (
                f"MEDIUM confidence secret not detected: {secret!r}"
            )

    def test_false_positives_not_flagged(self, detector):
        for text in self.NOT_SECRETS:
            matches = detector.detect(text)
            secret_matches = [m for m in matches if m.pii_type == PIIType.SECRET]
            assert len(secret_matches) == 0, (
                f"False positive: text incorrectly flagged as secret: {text!r}"
            )

    def test_secret_redaction(self, detector):
        text = "My API key is sk-proj-abc123def456ghi789jkl012mno345"
        redacted = detector.redact(text)
        assert "sk-proj-" not in redacted
        assert "[SECRET_REDACTED]" in redacted

    def test_env_file_content(self, detector):
        """Simulate an agent reading a .env file."""
        env_content = (
            'OPENAI_API_KEY="sk-proj-abc123def456ghi789jkl012mno345"\n'
            'AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n'
            'DATABASE_URL=postgres://user:pass@localhost/db\n'
        )
        matches = detector.detect(env_content)
        secret_matches = [m for m in matches if m.pii_type == PIIType.SECRET]
        # Should catch at least the OpenAI key and AWS key
        assert len(secret_matches) >= 2, (
            f"Expected at least 2 secrets in .env content, got {len(secret_matches)}"
        )
