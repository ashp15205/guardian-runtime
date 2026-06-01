# Guardian Runtime

**Local-first runtime governance for AI systems.**

Guardian Runtime is a Python SDK that sits between your AI application and any LLM — intercepting every prompt and response to enforce security policies, block data leaks, and detect threats. Everything runs locally on your machine. Your data never leaves your infrastructure.

---

## What it does

Guardian checks every prompt **before** it reaches the LLM and every response **before** it reaches the user.

```
User Input → [Guardian Input Guard] → LLM → [Guardian Output Guard] → User
```

---

## Features (v0.1.0)

### PII Detection
Detects sensitive personal data in prompts and responses before they reach any LLM.

**India DPDP Act (native):**
- Aadhaar numbers
- PAN card numbers
- UPI IDs

**Global:**
- Social Security Numbers (SSN)
- Credit card numbers
- Email addresses
- Phone numbers
- Passport numbers

### Secret & Credential Detection
Detects exposed API keys and credentials in prompts before they reach any LLM.

- OpenAI API keys (`sk-...`)
- Anthropic API keys (`sk-ant-...`)
- AWS Access Keys (`AKIA...`)
- GitHub tokens (`ghp_...`, `ghs_...`)
- Stripe live keys (`sk_live_...`)
- Razorpay live keys (`rzp_live_...`)
- Groq API keys (`gsk_...`)
- Generic `.env` style secrets (`KEY=value` patterns)

### Policy Engine
Declarative YAML-based policy configuration. Define rules once, enforce everywhere.

```yaml
version: "1.0"
agents:
  default:
    input_guard:
      pii_detection: true
      secret_detection: true
      jailbreak_detection: true
    output_guard:
      pii_detection: true
      hallucination_check: false
```

---

## Install

```bash
pip install guardian-runtime
```

Requires Python 3.9+

---

## Quickstart

```python
from guardian import scan_pii, scan_secrets

# Scan a prompt for PII
result = scan_pii("My Aadhaar is xxxx xxxx xxxx")
print(result.blocked)   # True
print(result.type)      # AADHAAR
print(result.severity)  # HIGH

# Scan a prompt for exposed secrets
result = scan_secrets("My key is sk-xxxxxxxxxxxxxxxxxxxx")
print(result.blocked)   # True
print(result.type)      # OPENAI_KEY
print(result.severity)  # HIGH
```

---

## Why local-first?

Every existing governance tool sends your prompts to their cloud servers. Guardian runs entirely on your machine.

- Prompts never leave your infrastructure
- Responses never leave your infrastructure
- Violation logs stored locally at `~/.guardian/logs/`
- One daily sync sends only: license key + check count (number only)
- No prompts. No responses. No API keys. Ever.

This matters for teams in regulated industries — finance, healthcare, government — where data cannot leave your infrastructure.

---

## Compliance

Guardian's PII detection is built for real regulatory requirements:

- **India DPDP Act 2023** — native Aadhaar, PAN, UPI detection
- **GDPR** — email, phone, passport detection
- **HIPAA** — sensitive personal data blocking
- **CCPA** — consumer data protection

---

## Development

```bash
pip install guardian-runtime[dev]
pytest tests/
```

68 unit tests. Zero network calls. All detection runs locally.

---

## Coming in v0.2.0

- Jailbreak and prompt injection detection
- Input Guard orchestrator (full pipeline)
- Output Guard with hallucination detection
- Token counting and cost tracking
- LangChain callback integration
- CLI: `guardian init`, `guardian status`, `guardian logs`

---

## License

Apache-2.0

---