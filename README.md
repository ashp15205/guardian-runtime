# Guardian Runtime

**Local-first runtime governance for AI systems.**

[![PyPI](https://img.shields.io/pypi/v/guardian-runtime.svg)](https://pypi.org/project/guardian-runtime/)
[![Python](https://img.shields.io/pypi/pyversions/guardian-runtime.svg)](https://pypi.org/project/guardian-runtime/)

Guardian Runtime is a Python SDK that sits between your AI application and any LLM — intercepting every prompt and response to enforce security policies, block data leaks, and detect threats. Everything runs locally on your machine. Your data never leaves your infrastructure.

**Built for teams everywhere** — startups and enterprises in any country. Compliance coverage spans **GDPR, HIPAA, CCPA**, and **India DPDP**; India-specific identifiers (Aadhaar, PAN, UPI) are included alongside global PII (SSN, cards, email, phone, passport).

My Product:
Guardian Runtime is a local-first Python SDK that acts as a security and governance layer between any AI application and any LLM. It intercepts every prompt before it reaches the model and every response before it reaches the user — blocking data leaks, jailbreaks, and policy violations in real time, entirely on the developer's machine.

Why Guardian Runtime ?:
AI agents are being deployed in production without any control layer. They leak sensitive data, get manipulated by malicious users, hallucinate facts, and burn API budgets — and developers only find out after the damage is done. Every existing tool (Langfuse, LangSmith, Helicone) only observes and logs. Nothing actively prevents bad behavior at the moment it happens.
Worse — those tools require your prompts to be sent to their cloud servers. For developers in regulated industries, that's a non-starter.
Guardian solves both problems: it prevents bad behavior in real time, and it does it entirely locally. Your data never leaves your machine.


> **Status (Jun 2026):** [0.1.1 on PyPI](https://pypi.org/project/guardian-runtime/) ships PII/secret scanners and the policy schema. **v1.0.0** (end of June) adds the full `Guardian.complete()` pipeline, guards, CLI, and local logging. See [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md).

---

## What it does

Guardian checks every prompt **before** it reaches the LLM and every response **before** it reaches the user.

```
User Input → [Guardian Input Guard] → LLM → [Guardian Output Guard] → User
```

---

## What works today (v0.2.0)

- **PII & secret scanning** — `scan_pii()`, `scan_secrets()`
- **Policy YAML** — `load_policy()`, `guardian validate`
- **LLM providers (v1):** OpenAI + Google Gemini (`provider: openai|gemini` in policy or kwarg)
- **Jailbreak detection**, **token count + cost estimate**, **max input tokens** (policy)
- **CLI** — `guardian init`, `validate`, `status`, `logs`
- **Local JSONL logs** at `~/.guardian/logs/`
- **92+ tests**, CI on push

**Coming for 1.0.0 (June 30):** PyPI release polish, demo video, multi-provider (July). See [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md).

---

## Features

### PII Detection (shipped)

### PII Detection
Detects sensitive personal data in prompts and responses before they reach any LLM.

**Global:**
- Social Security Numbers (SSN)
- Credit card numbers
- Email addresses
- Phone numbers
- Passport numbers

**India (DPDP Act) — included, not exclusive:**
- Aadhaar numbers
- PAN card numbers
- UPI IDs

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

### Policy Engine (schema shipped; runtime enforcement in v1.0)
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

### Scan only (no OpenAI key)

```python
from guardian import scan_pii, scan_secrets

result = scan_pii("My Aadhaar is xxxx xxxx xxxx")
print(result.blocked)   # True

result = scan_secrets("My key is sk-proj-xxxxxxxxxxxxxxxxxxxx")
print(result.blocked)   # True
```

### Full pipeline — Gemini (free tier, recommended for testing)

Get a free API key at [Google AI Studio](https://aistudio.google.com/apikey).

```bash
export GEMINI_API_KEY=your_key
```

```python
from guardian import Guardian

guardian = Guardian.from_policy("policies/gemini.yaml")
response = guardian.complete(
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)

if response.blocked:
    print(response.violations)
else:
    print(response.content)
    print(f"Provider: {response.provider}  Model: {response.model}")
```

Or pass the provider explicitly (uses policy defaults for model):

```python
guardian = Guardian.from_policy("policies/minimal.yaml")
response = guardian.complete(
    provider="gemini",
    model="gemini-2.0-flash",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### Full pipeline — OpenAI (paid)

```python
import os
from guardian import Guardian

os.environ["OPENAI_API_KEY"] = "sk-..."

guardian = Guardian.from_policy("policies/minimal.yaml")
response = guardian.complete(
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
```

```bash
guardian validate policies/minimal.yaml
guardian status
guardian logs --tail 10
```

### Legacy quickstart (scanners only)

```python
from guardian import scan_pii, scan_secrets

result = scan_pii("My Aadhaar is xxxx xxxx xxxx")
print(result.blocked, result.type)

result = scan_secrets("My key is sk-xxxxxxxxxxxxxxxxxxxx")
print(result.blocked, result.type)
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

- **GDPR** (EU) — email, phone, passport, general PII
- **HIPAA** (US health) — sensitive personal data blocking
- **CCPA** (California) — consumer data protection
- **DPDP Act 2023** (India) — Aadhaar, PAN, UPI + general PII
- **SOC2 / enterprise** — local-only processing, no prompt upload to vendor cloud

---

## Development

```bash
pip install guardian-runtime[dev]
pytest tests/   # 92+ tests (integration tests mock OpenAI)
```

---

## Roadmap

| Version | Target | Highlights |
|---------|--------|------------|
| **0.1.1** | ✅ Jun 2026 | PyPI, PII/secrets, policy schema — [install](https://pypi.org/project/guardian-runtime/) |
| **1.0.0** | Jun 30, 2026 | Full engine, guards, CLI, local logs — [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md) |
| **1.1.0** | Jul 2026 | LangChain callback, hallucination (optional), budget hard-stop |
| **2.0.0** | Sep 2026 | Portal, license server, ProductHunt — [PLAN.md](./PLAN.md) |

---

## Project docs

- [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md) — June sprint to 1.0.0
- [PLAN.md](./PLAN.md) — 16-week product & monetization plan
- [ARCHITECTURE.md](./ARCHITECTURE.md) — technical design
- [CHANGELOG.md](./CHANGELOG.md) — release history

---

## License

Apache-2.0

---