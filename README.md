# Guardian Runtime

**Open-source, local-first AI governance & cost optimization.**

[![PyPI](https://img.shields.io/pypi/v/guardian-runtime.svg)](https://pypi.org/project/guardian-runtime/)
[![Python](https://img.shields.io/pypi/pyversions/guardian-runtime.svg)](https://pypi.org/project/guardian-runtime/)
[![Tests](https://img.shields.io/badge/tests-109%20passed-brightgreen)](https://github.com/ashp15205/guardian-runtime)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

Guardian Runtime is a Python SDK that sits between your AI application and any LLM — **intercepting every prompt and response** to block data leaks, prevent jailbreaks, and **automatically reduce your token costs by up to 40%**. Everything runs locally. Your data never leaves your infrastructure.

```
User Input → [Input Optimizer] → [Input Guard] → LLM → [Output Guard] → User
                  ↓                    ↓                      ↓
           Saves tokens          Blocks PII/secrets     Blocks output PII
```

---

## Why Guardian?

| Problem | How Guardian Solves It |
|---------|----------------------|
| **PII leaks to LLM providers** | Local NER scanning blocks SSNs, Aadhaar, API keys _before_ the prompt leaves your server |
| **Exploding AI costs** | Input Optimizer compresses prompts, converts PDFs to markdown, trims chat history — saving 30-70% tokens |
| **No runtime controls** | YAML policy engine enforces per-agent rules without code changes |
| **Jailbreak attacks** | 40+ pattern detection blocks prompt injection attempts |
| **Compliance burden** | Built for GDPR, HIPAA, CCPA, and India DPDP out of the box |

Existing tools (Langfuse, Helicone, LangSmith) only **observe** traffic. Guardian **actively prevents** bad behavior at the moment it happens.

---

## Install

```bash
pip install guardian-runtime
```

Requires Python 3.9+

---

## Quickstart

### Full pipeline — providers (Big 3)

| Provider | Env var | Policy file | Default model |
|----------|---------|-------------|---------------|
| **Gemini** (free) | `GEMINI_API_KEY` | `policies/gemini.yaml` | `gemini-2.0-flash` |
| **Claude** | `ANTHROPIC_API_KEY` | `policies/anthropic.yaml` | `claude-3-5-haiku-latest` |
| **OpenAI** | `OPENAI_API_KEY` | `policies/minimal.yaml` | `gpt-4o-mini` |

```python
from guardian import Guardian

# Free testing with Gemini
guardian = Guardian.from_policy("policies/gemini.yaml")
response = guardian.complete(messages=[{"role": "user", "content": "Hello"}])
```

### Scan Without an LLM Key

```python
from guardian import scan_pii, scan_secrets

result = scan_pii("My Aadhaar is 0000 0000 0000")
print(result.blocked)   # True

result = scan_secrets("My key is sk-proj-xxxxxxxxxxxxxxxxxxxx")
print(result.blocked)   # True
```

### Optimize Prompts Standalone

```python
from guardian import optimize_input, convert_document

# Compress a messy conversation
result = optimize_input(messages, model="gpt-4o")
print(f"Saved {result.savings_pct:.0%} of tokens")

# Convert a heavy PDF to token-efficient markdown
doc = convert_document("contract.pdf")  # requires: pip install guardian-runtime[optimizer]
print(f"{doc.markdown_tokens} tokens (was {doc.original_size_bytes} bytes)")
```

---

## Features

### 🛡️ Security & Privacy

- **PII Detection** — SSN, credit cards, email, phone, passport, Aadhaar, PAN, UPI
- **Secret Detection** — OpenAI, Anthropic, AWS, GitHub, Stripe, Razorpay, Groq keys
- **Jailbreak Detection** — 40+ patterns (DAN, ignore instructions, role-play attacks)
- **Output Guard** — scans LLM responses for leaked PII before reaching the user
- **Action modes** — `block`, `redact`, or `flag` per entity type

### ⚡ Cost Optimization (Input Optimizer)

- **Prompt compression** — strips whitespace, deduplicates system prompts, removes empty messages
- **History trimming** — keeps last N turns, always preserves system prompt
- **Document conversion** — PDF/DOCX/XLSX → clean markdown (40-70% token savings)
- **Token budget enforcement** — warn or block when input exceeds limits
- **Proactive guidance** — logs suggestions when bloated prompts are detected
- **Savings tracking** — every `GuardianResponse` includes optimization metadata

### 🔧 Governance Engine

- **YAML policies** — define rules per agent, no code changes needed
- **Multi-agent** — different rules for different bots (HR-Bot vs Support-Bot)
- **Multi-provider** — OpenAI, Google Gemini, and Anthropic Claude (Big 3)
- **Local JSONL logs** — full audit trail at `~/.guardian/logs/`
- **CLI** — `guardian init`, `validate`, `status`, `logs`
- **FinOps** — token counting, cost estimation, per-session spend tracking

### 🔒 100% Local-First

- All governance runs on **your infrastructure**
- No prompts sent to Guardian servers — ever
- One daily sync sends only: license key + check count (number only)
- Built for regulated industries: finance, healthcare, government

---

## Policy Example

```yaml
version: "1.0"
name: "production"

agents:
  default:
    llm:
      provider: openai
      default_model: gpt-4o-mini
    input_guard:
      pii_detection: true
      jailbreak_detection: true
    output_guard:
      pii_detection: true
    optimizer:
      enabled: true
      whitespace_normalization: true
      max_history_messages: 20
      deduplicate_system_prompts: true
    cost:
      max_input_tokens: 8000
      per_session_limit: 1.00
```

---

## Compliance

Guardian's PII detection covers real regulatory requirements:

- **GDPR** (EU) — email, phone, passport, general PII
- **HIPAA** (US health) — sensitive personal data blocking
- **CCPA** (California) — consumer data protection
- **DPDP Act 2023** (India) — Aadhaar, PAN, UPI + general PII
- **SOC2 / Enterprise** — local-only processing, no prompt upload to vendor cloud

> ⚠️ Guardian is an assistive compliance tool, not legal advice. Always consult qualified counsel.

---

## CLI

```bash
guardian init --key gdn_free_xxxxx      # Setup (optional)
guardian validate policies/minimal.yaml  # Check policy syntax
guardian status                          # View usage stats
guardian logs --tail 10                  # View recent violation logs
```

---

## Architecture

```
guardian/
├── core/           # Engine, policy, models, storage, license
├── guards/         # Input & Output guards
│   └── validators/ # PII, secrets, jailbreak detectors
├── optimizer/      # Input Optimizer, Document Converter (MarkItDown)
├── finops/         # Token counter, cost calculator
├── providers/      # OpenAI, Gemini, Anthropic (Big 3)
├── logging/        # Local JSONL logger
└── cli/            # CLI commands
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full technical specification.

---

## Development

```bash
pip install guardian-runtime[dev]
pytest tests/   # 109 tests
```

---

## License

Apache-2.0