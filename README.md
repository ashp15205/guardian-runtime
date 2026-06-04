<p align="center">
  <h1 align="center">🛡️ Guardian Runtime</h1>
  <p align="center"><strong>The local-first AI firewall for developers.</strong></p>
  <p align="center">Cut LLM token costs · Block data leaks · Stop jailbreaks — all on your machine.</p>
</p>

<p align="center">
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/v/guardian-runtime.svg?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/pyversions/guardian-runtime.svg?style=flat-square" alt="Python"></a>
  <a href="https://github.com/ashp15205/guardian-runtime"><img src="https://img.shields.io/badge/tests-111%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="https://github.com/ashp15205/guardian-runtime"><img src="https://img.shields.io/badge/license-Proprietary-lightgrey?style=flat-square" alt="License"></a>
</p>

---

Guardian Runtime is a **Python SDK** that acts as a transparent security layer between your AI application and any LLM provider. It automatically compresses prompts to reduce token costs, blocks PII and API key leaks before they reach the model, and catches jailbreak attempts — **all running locally on your machine**. Your prompts never leave your infrastructure.

```text
  Your Prompt
      │
      ▼
┌─────────────────────────────────────────┐
│           GUARDIAN RUNTIME              │
│                                         │
│  ┌───────────┐   ┌──────────────────┐   │
│  │ Optimizer │   │   Input Guard    │   │
│  │           │   │                  │   │
│  │ -30~70%   │──▶│ PII · Secrets   │   │
│  │  tokens   │   │ Jailbreaks      │   │
│  └───────────┘   └────────┬─────────┘   │
│                           │             │
│         ┌─────────────────▼──────────┐  │
│         │       Output Guard         │  │
│         │  Scans AI response for PII │  │
│         └────────────────────────────┘  │
└─────────────────────────────────────────┘
      │
      ▼
  Safe Response + Cost Report
```

---

## 🚀 Quick Start

### 1. Install

```bash
pip install guardian-runtime
```

> Requires **Python 3.10+**. Includes the document converter (PDF/DOCX → Markdown) out of the box.

### 2. Set your API key

```bash
export GEMINI_API_KEY="your-google-ai-studio-key"   # free tier works!
```

### 3. Create a policy file (`policy.yaml`)

```yaml
version: "1.0"
agents:
  default:
    llm:
      provider: gemini
      default_model: gemini-2.5-flash
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
    cost:
      max_input_tokens: 8000
```

### 4. Use it

```python
from guardian import Guardian

guardian = Guardian.from_policy("policy.yaml")

response = guardian.complete(
    messages=[{"role": "user", "content": "Summarize this document for me."}]
)

print(response.content)              # safe, validated response
print(response.input_tokens)         # tokens consumed
print(response.estimated_cost_usd)   # cost in USD
print(response.optimization)         # token savings breakdown
```

---

## ✨ Why Guardian?

Observability tools (Langfuse, LangSmith, Helicone) **log** what went wrong — _after_ it happened.  
Guardian **stops** it _before_ it happens, **on your machine**.

| | Observability Tools | Guardian Runtime |
|---|---|---|
| **When it acts** | After the LLM call | **Before and after** |
| **Your data** | Sent to their cloud | **Stays on your machine** |
| **PII in prompt** | Logged | **Blocked** |
| **Exposed API keys** | Not detected | **Blocked** |
| **Token costs** | Tracked | **Actively reduced** |
| **Jailbreak attempts** | Logged | **Blocked** |

---

## 🔌 Supported Providers

Works out-of-the-box with the Big 3 LLM providers:

| Provider | Environment Variable | Default Model |
|---|---|---|
| **Google Gemini** | `GEMINI_API_KEY` | `gemini-2.5-flash` |
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | `claude-3-5-haiku-latest` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini` |

Override provider at runtime:
```python
response = guardian.complete(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    messages=[...]
)
```

---

## 🛡️ Security & Privacy Features

### PII Detection
Detects and blocks sensitive personal data with specialized patterns:

| Category | Detected Entities |
|---|---|
| **India (DPDP Act)** | Aadhaar (`xxxx xxxx xxxx`), PAN (`XXXXX0000X`), UPI (`name@bank`) |
| **Global** | SSN, Credit Cards, Email, Phone, Passport |
| **Action modes** | `block`, `redact`, or `flag` per entity type |

### Secret Leak Prevention
Stops developers from accidentally sending credentials to an LLM:

- OpenAI keys (`sk-...`) · AWS access keys (`AKIA...`) · GitHub tokens (`ghp_...`)
- Stripe keys (`sk_live_...`) · Razorpay keys (`rzp_live_...`) · Groq keys (`gsk_...`)
- Generic `.env` variable patterns

### Jailbreak Detection
40+ regex patterns covering:
- DAN variants and instruction overrides
- Role-play injections and encoding tricks
- System prompt extraction attempts

### Output Guard
Scans LLM responses for PII and secrets **before** they reach your users.

---

## 📉 Cost Optimization

| Feature | How it saves |
|---|---|
| **Prompt Compression** | Strips redundant whitespace, deduplicates system prompts, removes empty messages |
| **History Trimming** | Keeps last N turns, always preserves system prompt |
| **Document Conversion** | PDF, DOCX, XLSX, PPTX → clean Markdown (**30–70% token savings**) |
| **Token Budget Enforcement** | Warn or block when input exceeds your defined limit |
| **Cost Estimation** | Every response includes token count and USD cost estimate |

---

## 📊 Analysis Report

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

Example optimization result:
```json
{
  "original_tokens": 1840,
  "optimized_tokens": 620,
  "savings_pct": 0.66,
  "actions_taken": ["whitespace_normalization", "history_trimming"]
}
```

---

## ⚖️ Compliance Coverage

Guardian's detection covers major data protection regulations:

| Regulation | Coverage |
|---|---|
| **India DPDP Act 2023** | Aadhaar, PAN, UPI — native patterns |
| **GDPR** (EU) | Email, phone, passport, general PII |
| **HIPAA** (US Health) | Sensitive personal data blocking |
| **CCPA** (California) | Consumer data protection |

> **Note:** Guardian is an assistive compliance tool, not legal advice. Always consult qualified counsel for regulatory requirements.

---

## 🖥️ CLI

Guardian comes with a built-in command line interface:

```bash
guardian init --key gdn_free_xxxxx       # optional license setup
guardian validate policies/gemini.yaml   # check policy syntax
guardian status                          # view usage, tokens, and costs
guardian logs --tail 20                  # view recent violations
```

Example `guardian status` output:
```text
License: not configured (offline free tier)
Plan: free
Checks this month: 1 / 10000
Status: ACTIVE

--- Usage Analytics ---
Original Input Tokens:  1,840
Optimized Input Tokens: 620 (-1,220 saved)
Total Output Tokens:    19
Estimated Cost:         $0.000420 USD
```

---

## 🏗️ Local-First Architecture

Everything runs on your machine. Nothing is uploaded.

```text
Your Machine
├── guardian SDK         ← all processing happens here
├── ~/.guardian/
│   ├── config.json     ← license key (if using paid plan)
│   ├── usage.json      ← monthly check count
│   └── logs/           ← violation logs (never uploaded)
│       └── YYYY-MM-DD.jsonl
```

**What Guardian's servers never receive:**
- ❌ Your prompts
- ❌ Your LLM responses
- ❌ Your violation details
- ❌ Your API keys (OpenAI, Anthropic, etc.)

---

## 📁 Project Structure

```text
guardian/
├── core/           engine, policy, models, storage
├── guards/         input guard, output guard, validators
│   └── validators/ pii, secrets, jailbreak, hallucination
├── optimizer/      prompt compression, document converter
├── providers/      openai, gemini, anthropic
├── finops/         token counter, cost calculator
├── proxy/          localhost reverse proxy server
├── logging/        local JSONL logger
├── dashboard/      usage dashboard
└── cli/            init, validate, status, logs
```

---

## 🧪 Development

```bash
git clone https://github.com/ashp15205/guardian-runtime.git
cd guardian-runtime
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -q    # 111 tests
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full technical specification.

---

## 🔒 Privacy

- All scanning runs **on your infrastructure**
- Logs stored locally at `~/.guardian/logs/`
- Optional license sync sends **only** a hashed key + check count — never prompts or responses

---

<p align="center">
  <strong>Built with ❤️ for developers who care about AI safety and cost.</strong><br>
  <a href="https://pypi.org/project/guardian-runtime/">PyPI</a> · <a href="https://github.com/ashp15205/guardian-runtime">GitHub</a>
</p>
