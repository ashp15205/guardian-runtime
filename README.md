# Guardian Runtime

**Cut LLM token costs. Block data leaks. Ship safer AI.**

Guardian Runtime is a local-first Python SDK that sits between your AI application and any LLM. It automatically compresses prompts to reduce token costs, blocks PII and API key leaks before they reach the model, and catches jailbreak attempts — all on your machine. Your prompts never leave your infrastructure.

[![PyPI](https://img.shields.io/pypi/v/guardian-runtime.svg)](https://pypi.org/project/guardian-runtime/)
[![Python 3.9+](https://img.shields.io/pypi/pyversions/guardian-runtime.svg)](https://pypi.org/project/guardian-runtime/)
[![Tests](https://img.shields.io/badge/tests-111%20passed-brightgreen)](https://github.com/ashp15205/guardian-runtime)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

```text
User Input
    ↓
[Input Optimizer]  →  saves 30–70% tokens
    ↓
[Input Guard]      →  blocks PII, secrets, jailbreaks
    ↓
   LLM             →  your model, your API key
    ↓
[Output Guard]     →  scans response before it reaches user
    ↓
Safe Response + Analysis Report
```

---

## Why Guardian?

Observability tools (Langfuse, LangSmith, Helicone) log what went wrong — after it happened. Guardian stops it before it happens, on your machine.

| | Observability Tools | Guardian Runtime |
|---|---|---|
| When it acts | After the LLM call | **Before and after** |
| Your data path | Sent to their cloud | **Stays on your machine** |
| PII in prompt | Logged | **Blocked** |
| Exposed API keys | Not detected | **Blocked** |
| Token costs | Tracked | **Actively reduced** |
| Jailbreak attempts | Logged | **Blocked** |

---

## Install

```bash
pip install guardian-runtime
```

Optional extras:
```bash
pip install guardian-runtime[optimizer]   # PDF/DOCX → markdown conversion
pip install guardian-runtime[dev]         # testing tools
```

Requires **Python 3.9+**

---

## Quickstart (60 seconds)

### Free — test with Gemini (no billing required)

Get a free API key at [aistudio.google.com](https://aistudio.google.com/apikey)

```bash
export GEMINI_API_KEY=your_key_here
```

```python
from guardian import Guardian

guardian = Guardian.from_policy("policies/gemini.yaml")

response = guardian.complete(
    messages=[{"role": "user", "content": "What is the refund policy?"}]
)

if response.blocked:
    print("Blocked:", response.violations[0].type)
else:
    print(response.content)
```

### Scan without any LLM key

```python
from guardian import scan_pii, scan_secrets

# PII detection
result = scan_pii("My Aadhaar is xxxx xxxx xxxx")
print(result.blocked)    # True

# Secret detection
result = scan_secrets("My key is sk-proj-xxxxxxxxxxxxxxxxxxxx")
print(result.blocked)    # True
```

---

## Supported Providers

| Provider | Environment Variable | Policy file | Default Model |
|---|---|---|---|
| Google Gemini | `GEMINI_API_KEY` | `policies/gemini.yaml` | `gemini-2.0-flash` |
| Anthropic Claude | `ANTHROPIC_API_KEY` | `policies/anthropic.yaml` | `claude-3-5-haiku-latest` |
| OpenAI | `OPENAI_API_KEY` | `policies/minimal.yaml` | `gpt-4o-mini` |

Override provider at runtime:
```python
response = guardian.complete(
    provider="anthropic",
    model="claude-3-5-haiku-latest",
    messages=[...]
)
```

---

## Features

### Security & Privacy

- **PII Detection** — Aadhaar (`xxxx xxxx xxxx`), PAN (`XXXXX0000X`), UPI (`name@bank`), SSN (`xxx-xx-xxxx`), credit cards, email, phone, passport numbers
- **Secret Detection** — OpenAI keys (`sk-...`), AWS access keys (`AKIA...`), GitHub tokens (`ghp_...`), Stripe keys (`sk_live_...`), Razorpay keys (`rzp_live_...`), Groq keys (`gsk_...`), generic `.env` patterns
- **Jailbreak Detection** — 40+ patterns covering DAN variants, instruction overrides, role-play injections, encoding tricks, and system prompt extraction attempts
- **Output Guard** — scans LLM responses for PII and secrets before they reach users
- **Action modes** — `block`, `redact`, or `flag` per entity type

### Cost Optimization

- **Prompt compression** — strips redundant whitespace, deduplicates system prompts, removes empty messages
- **History trimming** — keeps last N turns, always preserves system prompt
- **Document conversion** — PDF, DOCX, XLSX → clean markdown (30–70% token savings)
- **Token budget enforcement** — warn or block when input exceeds your defined limit
- **Cost estimation** — every response includes token count and USD cost estimate

### Governance

- **YAML policy engine** — define rules per agent, no code changes needed to update policies
- **Multi-agent support** — different rules for different bots
- **Block / redact / flag modes** — choose the right action per violation type
- **Local audit logs** — full JSONL log at `~/.guardian/logs/` — never uploaded anywhere

### CLI

```bash
guardian init --key gdn_free_xxxxx       # optional license setup
guardian validate policies/gemini.yaml   # check policy syntax
guardian status                          # view usage this month
guardian logs --tail 20                  # view recent violations
```

---

## Policy Example

```yaml
version: "1.0"
agents:
  default:
    llm:
      provider: gemini
      default_model: gemini-2.0-flash
    input_guard:
      pii_detection: true
      jailbreak_detection: true
      pii_action: block
    output_guard:
      pii_detection: true
    optimizer:
      enabled: true
      whitespace_normalization: true
      max_history_messages: 10
      deduplicate_system_prompts: true
    cost:
      max_input_tokens: 8000
```

Validate before use:
```bash
guardian validate policies/gemini.yaml
```

---

## Analysis Report

Every `guardian.complete()` call returns a full analysis:

```python
response = guardian.complete(messages=[...])

print(response.content)              # safe, validated response
print(response.blocked)              # True if blocked
print(response.violations)           # list of what was caught
print(response.input_tokens)         # tokens used
print(response.estimated_cost_usd)   # cost in USD
print(response.optimization)         # tokens saved, savings %
```

Example output:
```python
{
  "blocked": False,
  "input_tokens": 620,
  "estimated_cost_usd": 0.0004,
  "optimization": {
    "original_tokens": 1840,
    "optimized_tokens": 620,
    "savings_pct": 0.66,
    "actions_taken": ["whitespace_normalization", "history_trimming"]
  },
  "violations": []
}
```

---

## Compliance

Guardian's detection covers major data protection regulations:

| Regulation | Coverage |
|---|---|
| **India DPDP Act 2023** | Aadhaar, PAN, UPI — native patterns |
| **GDPR** (EU) | Email, phone, passport, general PII |
| **HIPAA** (US Health) | Sensitive personal data blocking |
| **CCPA** (California) | Consumer data protection |

> Guardian is an assistive compliance tool, not legal advice. Always consult qualified counsel for regulatory requirements.

---

## Local-First Architecture

```text
Your Machine
├── guardian SDK         ← all processing happens here
├── ~/.guardian/
│   ├── config.json     ← license key (if using paid plan)
│   ├── usage.json      ← monthly check count
│   └── logs/           ← violation logs (never uploaded)
│       └── YYYY-MM-DD.jsonl
```

What Guardian's servers **never** receive:
- Your prompts
- Your LLM responses
- Your violation details
- Your API keys (OpenAI, Anthropic, etc.)

What the optional daily sync sends (once per day, HTTPS only):
- Your hashed license key
- A single number: how many checks you ran

---

## Project Structure

```text
guardian/
├── core/           engine, policy, models, storage
├── guards/         input guard, output guard, validators
│   └── validators/ pii, secrets, jailbreak, hallucination
├── optimizer/      prompt compression, document converter
├── providers/      openai, gemini, anthropic
├── finops/         token counter, cost calculator
├── logging/        local JSONL logger
└── cli/            init, validate, status, logs
```

---

## Development

```bash
git clone https://github.com/ashp15205/guardian-runtime.git
cd guardian-runtime
pip install -e ".[dev,optimizer]"
pytest tests/ -q    # 111 tests
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full technical specification.

---

## Privacy

- All scanning runs **on your infrastructure**
- Logs stored locally at `~/.guardian/logs/`
- Optional license sync sends **only** a hashed key + check count — never prompts or responses

---

## License

Apache-2.0 — free to use, modify, and distribute. See [LICENSE](LICENSE).
