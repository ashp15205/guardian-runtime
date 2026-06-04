<p align="center">
  <img src="https://img.shields.io/badge/GuardianRuntime-Local%20AI%20Firewall-00ff88?style=for-the-badge&logo=shield&logoColor=black" alt="GuardianRuntime" />
</p>

<h1 align="center">GuardianRuntime</h1>

<p align="center">
  <strong>A local-first AI security layer for Python developers.<br>
  Intercept every prompt and response. Block threats before they reach the LLM.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/v/guardian-runtime.svg?style=flat-square&color=00ff88" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/pyversions/guardian-runtime.svg?style=flat-square" alt="Python Versions"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/no%20signup-no%20key-00ff88?style=flat-square" alt="No signup required">
  <img src="https://img.shields.io/badge/100%25-local%20execution-00ff88?style=flat-square" alt="100% Local">
</p>

---

## What is GuardianRuntime?

**GuardianRuntime** is a Python SDK that sits between your AI application and any LLM provider (OpenAI, Gemini, Claude). Every prompt goes through a security pipeline **on your machine** before any network request fires. Every response is checked before it reaches your users.

It is **100% open source**, **free forever**, and requires **no signup, no API key, no account**.

```
Your App  →  [Input Guard]  →  [Optimizer]  →  LLM Provider
                  ↓                                   ↓
            Block / Redact                    [Output Guard]
                                                     ↓
                                             Your App gets clean response
```

---

## Why does this exist?

Sending raw user input directly to cloud LLMs is dangerous:

- **PII leaks** — a user pastes their Aadhaar, credit card, or SSN into a chatbot. The cloud provider now has it.
- **Credential exposure** — a developer accidentally includes an `sk-proj-...` key in their prompt. It gets sent to OpenAI's servers.
- **Jailbreaks** — users craft prompts like "Ignore your previous instructions and..." to override your system prompt.
- **Token waste** — unoptimized conversation histories bloat API costs by 30–70%.

GuardianRuntime solves all of this in a single `pip install`.

---

## Installation

```bash
pip install guardian-runtime
```

Optional one-time setup (creates local log directory):

```bash
guardian_runtime init
guardian_runtime status
```

That's it. No license key. No account. No cloud calls.

---

## Quick Start (60 seconds)

### Step 1 — Create a policy file

```yaml
# policies/prod.yaml
version: "1.0"
name: "production"
interactive_mode: off

agents:
  default:
    llm:
      provider: openai
      default_model: gpt-4o

    input_guard:
      pii_detection: true
      jailbreak_detection: true
      pii_action: block      # or 'redact' to mask and continue

    optimizer:
      enabled: true
      whitespace_normalization: true
      max_history_messages: 10
```

### Step 2 — Wrap your LLM call

Replace direct API calls with `GuardianRuntime`:

```python
import os
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

os.environ["OPENAI_API_KEY"] = "sk-proj-..."

# Loads rules from your YAML policy
gr = GuardianRuntime.from_policy("policies/prod.yaml")

try:
    response = gr.complete(
        messages=[{"role": "user", "content": "Hello, help me with my account."}],
        raise_on_block=True
    )
    print(response.content)

except GuardianRuntimeBlockedError as e:
    # The LLM was never called. Threat neutralized locally.
    print(f"Blocked: {e}")
```

### Step 3 — The response object

Every `gr.complete()` call returns a `GuardianRuntimeResponse`:

```python
response.content           # str — the LLM's reply (or block message)
response.blocked           # bool — True if the request/response was blocked
response.violations        # list[Violation] — what was detected
response.input_tokens      # int — tokens sent to the LLM
response.output_tokens     # int — tokens in the response
response.estimated_cost_usd  # float — estimated API cost for this call
response.optimization      # dict — token savings stats (if optimizer enabled)
```

---

## Security Guards

### PII Detection

Detects sensitive personal data using zero-model, regex-based scanning. Runs in microseconds.

| Type | Example Pattern |
|---|---|
| Aadhaar (India) | `1234 5678 9012` |
| PAN Card | `ABCDE1234F` |
| UPI ID | `name@ybl`, `name@paytm` |
| Credit / Debit Card | 16-digit card numbers |
| SSN (US) | `123-45-6789` |
| Email Address | `user@example.com` |
| Phone Number | `+91 98765 43210` |

Configure the action in your policy:
```yaml
input_guard:
  pii_detection: true
  pii_action: block    # 'block' stops the request | 'redact' masks and continues
```

### Credential / Secret Detection

Catches hardcoded API keys and credentials before they leave your machine.

```
AKIAIOSFODNN7EXAMPLE      → AWS Access Key
sk-proj-...                → OpenAI Secret Key
ghp_...                    → GitHub Personal Access Token
sk_live_...                → Stripe Secret Key
-----BEGIN RSA PRIVATE KEY → Private Key Block
```

### Jailbreak & Prompt Injection Defense

Blocks 50+ adversarial prompt patterns:

- **Instruction overrides:** "Ignore previous instructions", "Forget your system prompt"
- **DAN attacks:** "Developer Mode enabled", "Do Anything Now"
- **Encoding tricks:** Base64 / Hex / ROT13 payload wrappers
- **Role-play bypasses:** "Pretend you have no restrictions"

---

## Token Optimizer

The built-in optimizer reduces prompt payload size before sending to the LLM. This directly cuts your API costs.

```python
from guardian_runtime import optimize_input
from guardian_runtime.core.policy import OptimizerConfig

messages = [{"role": "user", "content": "   Please    explain     this.   "}]

result = optimize_input(
    messages=messages,
    config=OptimizerConfig(enabled=True, whitespace_normalization=True)
)

print(f"Reduced by {result.savings_pct:.1f}%")
print(f"Tokens saved: {result.original_tokens - result.optimized_tokens}")
```

Typical savings: **30–70%** on conversation histories with whitespace and repetition.

---

## Document Ingestion

Convert PDFs and DOCX files into clean, token-efficient Markdown for context injection:

```python
from guardian_runtime import convert_document

doc = convert_document("report.pdf")

print(f"Title:  {doc.title}")
print(f"Tokens: {doc.token_count}")
print(doc.content)  # clean Markdown ready for LLM injection
```

---

## CLI Reference

```bash
# Initialize local environment (creates ~/.guardian_runtime/logs/)
guardian_runtime init

# Show usage stats and system status
guardian_runtime status

# Tail live request logs
guardian_runtime logs --tail 20

# Validate a policy file for syntax errors
guardian_runtime validate policies/prod.yaml

# Start the proxy server (intercept OpenAI-compatible requests)
guardian_runtime proxy --port 8080

# Launch the local analytics dashboard
guardian_runtime dashboard
```

---

## Providers

GuardianRuntime supports all major LLM providers. Just set the appropriate API key as an environment variable:

| Provider | `provider` value | Environment Variable |
|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` |
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` |

Switch providers in your policy:
```yaml
agents:
  default:
    llm:
      provider: gemini
      default_model: gemini-2.0-flash
```

---

## Local Audit Logs

Every request — whether blocked or passed — is logged locally at `~/.guardian_runtime/logs/` in structured JSONL format. Nothing is ever sent to any external server.

```bash
guardian_runtime logs --tail 5
```

```
[BLOCK] PII: Aadhaar number detected in input payload
[BLOCK] SECRET: OpenAI key (sk-proj-...) found in prompt
[PASS]  Clean prompt forwarded to gpt-4o
[OPT]   Optimizer: -42% token reduction (1,200 → 696 tokens)
[BLOCK] OUTPUT_PII: Email address detected in LLM response
```

Extract programmatic cost reports:

```python
report = gr.get_cost_report(agent_id="default")
print(report["total_estimated_cost_usd"])
```

---

## Development Mode

For local development, use `warn_ask` mode instead of hard blocking. GuardianRuntime will print a security alert to stderr and ask you whether to proceed:

```yaml
interactive_mode: warn_ask   # asks you in the terminal before blocking
```

```
🚨 GUARDIAN_RUNTIME SECURITY ALERT
GuardianRuntime detected the following issues in your prompt:
  • [PII] Aadhaar number found in content

Do you still want to send this prompt to OpenAI? [y/N]
```

---

## Use Cases

| Scenario | Policy Config |
|---|---|
| Terminal chatbot / coding assistant | `interactive_mode: warn_ask`, all guards on |
| Production web app | `interactive_mode: off`, `pii_action: block` |
| Document Q&A pipeline | Optimizer + Document converter enabled |
| Multi-agent orchestration | Per-agent policies with isolated guard configs |

See the [`docs/`](./docs/) folder for detailed implementation guides for each use case.

---

## Run Tests

```bash
# Using the included test suite
source .venv/bin/activate
python final_test.py
```

Expected output: All PII blockers, jailbreak detection, document parsers, and optimizer functions validated.

---

## Project Structure

```
guardian_runtime/
├── core/
│   ├── engine.py        # Main pipeline orchestrator
│   ├── policy.py        # YAML policy loader & validator
│   ├── models.py        # Response and violation data models
│   └── storage.py       # Local usage analytics
├── guards/
│   ├── input_guard.py   # PII + secret + jailbreak detection
│   ├── output_guard.py  # LLM response scanner
│   └── validators/      # Individual detection modules
├── optimizer/           # Token reduction engine
├── providers/           # OpenAI / Gemini / Anthropic adapters
├── finops/              # Token counter + cost estimator
├── logging/             # Local JSONL audit logger
├── dashboard/           # Web analytics dashboard server
└── cli/                 # CLI commands (init, status, logs, proxy...)
policies/                # Example YAML policy files
docs/                    # Use-case implementation guides
```

---

## License

Released under the [MIT License](./LICENSE) — free to use, modify, and distribute.

**Maintained by:** Ashish Patil ([@ashp15205](https://github.com/ashp15205))
