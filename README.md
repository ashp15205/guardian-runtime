<p align="center">
  <img src="https://img.shields.io/badge/GuardianRuntime-Local%20AI%20Firewall-10b981?style=for-the-badge&logo=shield&logoColor=white" alt="GuardianRuntime Logo" />
</p>

<h1 align="center">GuardianRuntime</h1>

<p align="center">
  <strong>The Enterprise Local-First AI Firewall for Python Developers.</strong><br>
  Intercept PII leaks, block credential exposures, stop jailbreaks, and optimize token payload costs natively on your infrastructure before data ever reaches the LLM provider.
</p>

<p align="center">
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/v/guardian-runtime.svg?style=flat-square&color=10b981" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/pyversions/guardian-runtime.svg?style=flat-square" alt="Python Versions"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT License"></a>
  <a href="https://github.com/ashp15205/guardian-runtime/actions"><img src="https://img.shields.io/github/actions/workflow/status/ashp15205/guardian-runtime/ci.yml?style=flat-square" alt="Build Status"></a>
  <a href="#compliance"><img src="https://img.shields.io/badge/Compliance-GDPR%20%7C%20HIPAA%20%7C%20DPDP-yellow?style=flat-square" alt="Compliance Status"></a>
</p>

---

## 📖 Executive Summary

**GuardianRuntime** (`pip install guardian-runtime`) is a lightweight, zero-dependency Python SDK designed to sit between your application logic and the Large Language Model (OpenAI, Google Gemini, Anthropic Claude). 

Sending raw user input to cloud LLMs exposes your organization to **Prompt Injection attacks**, **Compliance breaches** (PII leaks), and **Credential exposure** (hardcoded keys). 

GuardianRuntime acts as a **zero-trust local firewall**. It executes high-speed regex and heuristic scanning on your own infrastructure to neutralize threats *before* any network request is initiated.

## 🚀 Key Capabilities

- **🔒 PII & Data Privacy Shield:** Detects and blocks Aadhaar, PAN, SSNs, Credit Cards, UPI IDs, Emails, and Phone Numbers (GDPR, HIPAA, DPDP Act compliance).
- **🔑 Secret Credential Guard:** High-precision prefix matching blocks AWS, OpenAI, GitHub, Stripe, and 10+ other credential formats from leaking.
- **🛡️ Jailbreak & Injection Defense:** Blocks over 50+ adversarial AI patterns including "DAN", instruction overrides, and role-play bypasses.
- **⚡ Token Optimization Engine:** Reduces prompt token payloads by 30-70% via whitespace normalization and history compression.
- **📄 Document Ingestion Pipeline:** Converts heavy PDF and DOCX files into raw, token-efficient Markdown representations.
- **📊 Local JSONL Telemetry:** 100% of transactions (blocks, optimizations, passes) are logged locally for enterprise auditability and ROI tracking.

---

## ⚡ Quick Start Installation

```bash
pip install guardian-runtime
```

Initialize your local environment:
```bash
guardian_runtime init --key YOUR_LICENSE_KEY
guardian_runtime status
```

---

## 🛠️ Implementation (60 Seconds)

GuardianRuntime integrates seamlessly with a single YAML policy file, abstracting the complexity of provider-specific APIs.

### 1. Define Policy (`policies/prod.yaml`)

```yaml
version: "1.0"
name: "production"
interactive_mode: off  # Use 'warn_ask' for local development

agents:
  default:
    llm:
      provider: openai
      default_model: gpt-4o

    input_guard:
      pii_detection: true
      jailbreak_detection: true
      pii_action: block

    optimizer:
      enabled: true
      whitespace_normalization: true
      max_history_messages: 10
```

### 2. Wrap Your API Calls

Replace direct API calls with the `GuardianRuntime` engine:

```python
import os
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

os.environ["OPENAI_API_KEY"] = "sk-proj-your-api-key"

# Engine automatically loads rules from your YAML configuration
gr = GuardianRuntime.from_policy("policies/prod.yaml")

try:
    # Payload is scanned locally in milliseconds
    response = gr.complete(
        messages=[{"role": "user", "content": "Hello, please review my account."}],
        raise_on_block=True
    )
    print("AI Response:", response.content)

except GuardianRuntimeBlockedError as e:
    # Execution aborted; LLM is never called. Threat mitigated.
    print(f"SECURITY ALERT: {e}")
```

---

## 🛡️ Core Security Engines

### PII Data Protection
Built-in detectors require zero NLP models and run instantaneously:
- **India (DPDP):** Aadhaar (`XXXX XXXX XXXX`), PAN (`AAAAA0000A`), UPI IDs (allowlisted suffixes like `@ybl`, `@paytm`).
- **US/EU (HIPAA/GDPR):** Credit Cards (16-digits), SSN (`XXX-XX-XXXX`), Passports, Emails, Phone Numbers.

### Credential Protection
Exact prefix matching guarantees zero false-positives on production environments:
- `AKIAXXXXXXXXX` (AWS Access Keys)
- `sk-proj-...` (OpenAI Keys)
- `ghp_...` (GitHub Tokens)
- `sk_live_...` (Stripe Secret Keys)
- `-----BEGIN RSA PRIVATE KEY-----` (Private Key blocks)

### Jailbreak Defense
Blocks over 50 prompt injection vectors locally:
- **Instruction Override:** "Ignore previous instructions", "Forget your system prompt"
- **DAN Modifiers:** "Developer Mode enabled", "Do anything now"
- **Encoding Attacks:** Base64, Hexadecimal, and ROT13 payload wrappers.

---

## 📉 Token Optimization & ROI

GuardianRuntime isn't just for security—it pays for itself by reducing API overhead.

```python
from guardian_runtime import optimize_input
from guardian_runtime.core.policy import OptimizerConfig

messages = [{"role": "user", "content": "   Please    explain     this.   "}]

result = optimize_input(
    messages=messages,
    config=OptimizerConfig(enabled=True, whitespace_normalization=True)
)

print(f"Payload reduced by {result.savings_pct}%")
```

### Document to Markdown Conversion
PDFs drain token limits due to embedded layout formatting. `convert_document()` extracts raw semantic text into clean Markdown.

```python
from guardian_runtime import convert_document

doc = convert_document("financial_report.pdf")
print(f"Extracted {doc.token_count} clean tokens for context injection.")
```

---

## 📊 Enterprise Auditing & Telemetry

GuardianRuntime never sends telemetry to external servers. All operations are written locally in structured `JSONL` format to `~/.guardian_runtime/logs/`.

Extract analytics programmatically to track ROI and compliance:

```python
report = gr.get_cost_report(agent_id="default")

print(f"Requests Processed: {report['total_requests']}")
print(f"Threats Mitigated:  {report['blocked_requests']}")
print(f"Tokens Saved:       {report['total_tokens_saved']}")
```

Or utilize the built-in CLI for real-time operations:
```bash
$ guardian_runtime logs --tail 5
[BLOCK] PII: Aadhaar detected in input payload
[BLOCK] Secret: AWS Access Key exposure
[PASS]  Clean prompt forwarded to LLM
[OPT]   Tokens optimized (-42% payload reduction)
```

---

## 🧪 Testing Environment

Run the comprehensive master test suite to validate all guards locally:

```bash
source .venv/bin/activate
python final_test.py
```
*Expected Output:* Validates PII blockers, Jailbreak detection, Document parsers, and Optimizer functions via 100% test coverage.

---

## 📜 License & Compliance

Released under the [MIT License](./LICENSE). 

GuardianRuntime is designed to assist organizations in complying with data localization laws (DPDP Act, GDPR) by ensuring sensitive data detection occurs entirely on host infrastructure. 

**Maintained by:** Ashish Patil ([@ashp15205](https://github.com/ashp15205))
