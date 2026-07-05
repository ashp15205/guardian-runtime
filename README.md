<p align="center">
  <img src="https://img.shields.io/badge/Guardian_Runtime-v1.3.0-00ff88?style=for-the-badge&logo=shield&logoColor=black" alt="v1.3.0">
  <img src="https://img.shields.io/github/stars/ashp15205/guardian-runtime?style=for-the-badge&logo=github&color=gold" alt="GitHub Stars">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="MIT">
  <img src="https://img.shields.io/pypi/pyversions/guardian-runtime.svg?style=for-the-badge&logo=python" alt="Python">
</p>

<h1 align="center">Guardian Runtime</h1>

<p align="center">
  <strong>Guardian Runtime sits securely on your machine, acting as a bodyguard for your code.<br>
  Whenever you use AI tools like Cursor or Claude Code, it scans every prompt locally to stop sensitive secrets and PII from reaching the cloud.<br>
  It also tracks your API spending to prevent surprise bills, all without slowing you down.</strong>
</p>

## Star History

<a href="https://www.star-history.com/?type=date&repos=ashp15205%2Fguardian-runtime">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=ashp15205/guardian-runtime&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=ashp15205/guardian-runtime&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=ashp15205/guardian-runtime&type=date&legend=top-left" />
 </picture>
</a>

<p align="center">
  <a href="https://buymeacoffee.com/ashishp05"><img src="https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me A Coffee"></a>
</p>

<p align="center">
  🌐 <strong>Docs & Demo:</strong> <a href="https://ashp15205.github.io/guardian-runtime/">ashp15205.github.io/guardian-runtime</a><br>
  📦 <strong>PyPI:</strong> <a href="https://pypi.org/project/guardian-runtime/">pypi.org/project/guardian-runtime</a>
</p>

---

## What is Guardian Runtime?

Guardian Runtime is a **local HTTP proxy** that runs entirely on your own machine. It sits between your AI coding tool and the cloud, inspecting every prompt before it leaves your infrastructure.

```
  Your AI Tool                  Guardian Runtime              Cloud LLM
  (Claude Code / Cursor)        (localhost:8080)              (OpenAI / Anthropic / Gemini)
         │                             │                              │
         │  Prompt + Files             │                              │
         │ ──────────────────────────▶ │                              │
         │                             │    Secret Scanner            │
         │                             │    PII Detector              │
         │                             │    Doc Converter (PDF→MD)    │
         │                             │    Token Counter             │
         │                             │    Budget Guard              │
         │                             │    Jailbreak Detector        │
         │                             │                              │
         │  [BLOCKED] ◀──────────────  │  ✗ Threat found              │
         │  "line 3: AWS key. y/n?"    │                              │
         │                             │ ───────────────────────────▶ │
         │ Optimized Response ◀─────── │ ◀──────────────────────────  │
```

**All data stays on your machine.** Your API keys live in a local `.env` file. All logs write to `~/.guardian_runtime/`. Nothing leaves without clearance.

---

## Table of Contents

- [The Problem](#the-problem)
- [Architecture & Security Pipeline](#architecture--security-pipeline)
- [Features](#features)
- [Supported Tools & Providers](#supported-tools--providers)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Interactive Block — How It Looks](#interactive-block--how-it-looks)
- [Use Cases](#use-cases)
- [CLI Reference](#cli-reference)
- [Policy Configuration](#policy-configuration)
- [License](#license)

---

## The Problem

| Risk | Description |
| :--- | :--- |
| **💸 Cost Runaways** | Agents operate in loops. A stuck agent can rack up a **$100+ API bill overnight** with zero warning. |
| **🔒 Secret Leaks** | Agents read your entire workspace. One `.env` file with an `AWS_SECRET_KEY` in context, and that credential silently travels to an Anthropic or OpenAI cloud server. |
| **🏛 Compliance Risk** | Sending unauthorized PII (SSNs, emails, Aadhaar) to public LLM APIs violates GDPR, HIPAA, and India's DPDP Act. |

---

## Architecture & Security Pipeline

Every request passes through a strict local pipeline before reaching the cloud:

```
Agent / Dev                  Guardian Runtime (local)              Cloud LLM
     │                              │                                  │
     │  1. Prompt + Files           │                                  │
     │ ────────────────────────────▶│                                  │
     │                              │ [File Router]                    │
     │                              │ ├─ Code files  → Secret Scanner  │
     │                              │ └─ Doc files   → MarkItDown → MD │
     │                              │                                  │
     │                              │ [Security Guards]                │
     │                              │ ├─ Regex: AWS / GitHub / OAI keys│
     │                              │ ├─ PII: SSN / Aadhaar / email    │
     │                              │ ├─ Jailbreak patterns (40+)      │
     │                              │ └─ Report exact line number      │
     │                              │                                  │
     │                              │ [Interactive Block]              │
     │  "line 3: secret. y/n?" ◀──  │  Ask user before dropping        │
     │                              │                                  │
     │                              │ [Token Optimizer]                │
     │                              │ ├─ tiktoken counting             │
     │                              │ ├─ Whitespace normalization      │
     │                              │ └─ Terse Mode injection          │
     │                              │                                  │
     │                              │ [FinOps Budget Guard]            │
     │                              │ └ Block if daily_budget exceeded │
     │                              │                                  │
     │                              │  2. Clean, verified prompt       │
     │                              │ ────────────────────────────────▶│
     │                              │                                  │
     │                              │  3. LLM Response                 │
     │                              │◀──────────────────────────────── │
     │                              │                                  │
     │                              │ [Output Guard]                   │
     │                              │  Audit response for leaks        │
     │                              │                                  │
     │  4. Optimzied Response       │                                  │
     │◀──────────────────────────── │                                  │
```

---

## Features

| # | Feature | Description |
| :- | :--- | :--- |
| 01 | 🔑 **Secret Scanner** | Detects AWS keys, GitHub tokens, OpenAI/Anthropic keys, Stripe secrets, Razorpay, Groq. Reports the exact **line number**. |
| 02 | 👤 **PII Detector** | Catches Aadhaar, PAN, SSN, credit cards, email, phone, passport. Fully offline. |
| 03 | 🛡️ **Jailbreak Guard** | 40+ patterns detecting DAN mode, role-play attacks, and prompt injection. |
| 04 | 💬 **Interactive y/n Override** | Replies inside your chat: *"Secret on line 3. Proceed? y/n"* — stays in the flow. Works on OpenAI, Anthropic, and Gemini formats. |
| 05 | 📄 **Document Converter** | PDF, DOCX, XLSX → Markdown via Microsoft MarkItDown. Also available as a CLI command. |
| 06 | 💸 **Hard Budget Caps** | Set `daily_budget: 5.00`. Guardian blocks any request that would push you over. |
| 07 | ⚡ **Terse Mode** | Injects a system prompt forcing concise replies. Cuts output tokens **40–70%** in benchmarks. |
| 08 | 🌐 **Universal Proxy** | Speaks OpenAI, Anthropic, AND native Gemini (`/v1beta/models/{model}:generateContent`) formats. |
| 09 | 📊 **Session Analytics** | Tracks cost, tokens, blocks, and conversions locally. Query via `guardian_runtime analytics` or `GET /stats`. |

---

## Supported Tools & Providers

| Category | Tools |
| :--- | :--- |
| **Visual IDEs** | Cursor, Windsurf, VS Code (via Cline/RooCode) |
| **Terminal Agents** | Claude Code, Aider, GitHub Copilot CLI |
| **Frameworks** | LangChain, AutoGen, LlamaIndex, CrewAI |
| **LLM Providers** | OpenAI, Anthropic Claude, Google Gemini |
| **API Formats** | OpenAI REST, Anthropic REST, Gemini v1beta (native) |

---

## Installation

```bash
# Full install (all providers + document converter + ML scanner)
pip install "guardian_runtime[all]"

# Or install only what you need:
pip install "guardian_runtime[openai]"
pip install "guardian_runtime[anthropic]"
pip install "guardian_runtime[gemini]"
```

*Done. No signup. No cloud account required.*

---

## Quickstart

### 1. Start the proxy

```bash
guardian_runtime proxy --port 8080
```

### 2. Connect your AI tool

```bash
# Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8080
claude

# Aider
export OPENAI_API_BASE=http://localhost:8080/v1
aider

# Gemini CLI
export HTTPS_PROXY=http://localhost:8080
gemini

# Cursor / Windsurf
# Settings → AI → Base URL → http://localhost:8080
```

### 3. Python SDK (optional)

```python
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

gr = GuardianRuntime()  # zero-config

try:
    response = gr.complete(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_input}],
        raise_on_block=True
    )
    print(response.content)
except GuardianRuntimeBlockedError as e:
    print(f"Blocked: {e.response.violations[0].detail}")
```

---

## Interactive Block — How It Looks

When Guardian detects a secret or PII, instead of crashing your session, it replies **inside your chat window** as the assistant:

```
[GUARDIAN_RUNTIME BLOCKED] Your request was intercepted.

Violation : secret
Detail    : AWS Access Key ID found on line 3
Line      : AWS_KEY=AKIAIOSFODNN7EXAMPLE

Type y/n in your next message to proceed or cancel.
```

- Type **`y`** → Guardian bypasses the scanner for that single request only.
- Type **`n`** → Block holds. The secret never leaves your machine.

---

## 📈 Local Analytics Web Dashboard

Guardian Runtime includes a built-in, premium web dashboard to visualize your local AI usage over time, entirely offline. 

**What it provides:**
- **Real-time KPIs**: Track Total Cost (Today), Tokens Processed, Threats Blocked, and Docs Converted.
- **Visual Analytics**: Interactive dual-axis charts showing token consumption vs. blocked requests over a 7-day period.
- **Privacy-first**: Fully offline and runs entirely on your local machine with a beautiful, responsive dark-mode UI.

**How to access it:**
1. Start the proxy server with the auto-open flag:
   ```bash
   guardian_runtime proxy --port 8080 -d
   ```
2. Or manually navigate to:
   👉 **[http://localhost:8080/dashboard](http://localhost:8080/dashboard)**

---

## Use Cases

### Terminal Agents (Claude Code, Aider)
```bash
guardian_runtime proxy --port 8080
export ANTHROPIC_BASE_URL=http://localhost:8080
claude  # All Claude Code traffic is now protected
```

### Visual IDEs (Cursor, Windsurf)
```
1. guardian_runtime proxy --port 8080
2. Cursor Settings (Cmd+,) → Models → Override Base URL
3. Set to: http://localhost:8080
```

### Agentic Frameworks (LangChain, AutoGen)
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="http://localhost:8080/v1",
    api_key="sk-proj-..."
)
```

### Document Conversion
```bash
# Convert before uploading to any AI chat
guardian_runtime convert report.pdf --out report.md
```

---

## CLI Reference

| Command | Description |
| :--- | :--- |
| `guardian_runtime proxy --port 8080` | Start the local security proxy |
| `guardian_runtime convert <file> --out <file.md>` | Convert PDF/DOCX/XLSX to Markdown |
| `guardian_runtime scan "<text>"` | Manually scan any text for threats |
| `guardian_runtime analytics` | Show today's cost, tokens, and blocks |
| `guardian_runtime analytics --all` | Show all-time historical analytics |
| `guardian_runtime logs` | Tail the live JSONL event stream |
| `guardian_runtime init` | Generate a boilerplate `policy.yaml` |
| `guardian_runtime validate` | Check `policy.yaml` for syntax errors |
| `guardian_runtime status` | Show health of local installation |
| `guardian_runtime clean` | Delete all local data and logs |
| `GET /stats` | Live REST endpoint (while proxy is running) |

---

## Policy Configuration

Run `guardian_runtime init` to generate a `policy.yaml`, then customize:

```yaml
version: "1.0"
agents:
  default:
    llm:
      provider: openai
      default_model: gpt-4o

    input_guard:
      scanner_enabled: true         # Secret + PII scanning
      jailbreak_detection: true     # 40+ jailbreak patterns
      scanner_action: block         # "block" or "warn"

    cost:
      daily_budget: 5.00            # Hard block at $5/day
      max_input_tokens: 20000       # Block oversized context windows

    optimizer:
      enabled: true
      terse_mode: true              # Cuts output tokens 40–70%
      max_history_messages: 20      # Trim old chat history
```

---

## License

Released under the **MIT License**. Zero tracking. Zero cloud dependencies. Your code is yours.
