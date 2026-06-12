<p align="center">
  <img src="https://img.shields.io/badge/GuardianRuntime-Local%20AI%20Firewall-00ff88?style=for-the-badge&logo=shield&logoColor=black" alt="GuardianRuntime" />
</p>

<h1 align="center">Guardian Runtime</h1>

<p align="center">
  <strong>A Zero-Latency FinOps & Security Firewall for AI Applications.<br>
  Intercept every prompt and response locally. Stop data leaks and runaway token costs.</strong>
</p>

<p align="center">
  <a href="https://buymeacoffee.com/ashishp05"><img src="https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me A Coffee"></a>
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/pyversions/guardian-runtime.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Versions"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  🌐 <strong>Website & Docs:</strong> <a href="https://ashp15205.github.io/guardian-runtime/">https://ashp15205.github.io/guardian-runtime/</a><br>
  📦 <strong>Available on PyPI:</strong> <a href="https://pypi.org/project/guardian-runtime/">https://pypi.org/project/guardian-runtime/</a>
</p>

---

<div align="center">
  <a href="https://ashp15205.github.io/guardian-runtime/">
    <img src="docs/screenshot.png" alt="Guardian Runtime Dashboard" width="800">
  </a>
</div>

## 📖 Table of Contents
- [🛑 The Core Problem: Why You Need Guardian](#-the-core-problem-why-you-need-guardian)
- [🟢 The Solution: What is Guardian Runtime?](#-the-solution-what-is-guardian-runtime)
- [🏗 Architecture](#-architecture)
- [🚀 Quickstart & Installation](#-quickstart--installation)
- [🎯 Comprehensive Use Cases (Where & How to Use)](#-comprehensive-use-cases-where--how-to-use)
  - [1. Terminal Coding Agents (Claude Code, Aider)](#1-terminal-coding-agents-claude-code-aider)
  - [2. Visual IDEs (Cursor, Windsurf)](#2-visual-ides-cursor-windsurf)
  - [3. Production Python Applications (SDK)](#3-production-python-applications-sdk)
  - [4. Agentic Frameworks (LangChain, AutoGen)](#4-agentic-frameworks-langchain-autogen)
  - [5. Data Prep for Web UIs (Document Conversion)](#5-data-prep-for-web-uis-document-conversion)
- [💻 Complete CLI Command Reference](#-complete-cli-command-reference)
- [⚙️ Advanced Configuration (Policy YAML)](#️-advanced-configuration-policy-yaml)
- [📜 License](#-license)

---

## 🛑 The Core Problem: Why You Need Guardian

As AI coding agents (Claude Code, Cursor, Aider) become standard developer tools, they introduce two massive, hidden risks, and one regulatory headache:

### 💸 1. The FinOps Risk: Cost Runaways
Autonomous agents operate in loops. If an agent gets stuck retrying a bug fix or accidentally dumps a massive 1GB log file into its context window, you can wake up to a **$100 API bill overnight**. 
**The Problem:** You have zero visibility or control over session costs until the provider's bill arrives at the end of the month.

### 🔒 2. The Security Risk: Data Exfiltration
Coding agents require full local codebase access to be useful. However, if you accidentally leave an `AWS_SECRET_KEY` or a database password in a `.env` file, the agent will silently upload it to a third-party LLM provider (OpenAI, Anthropic).
**The Problem:** Current observability tools (like Langfuse) only log the leak *after* the credentials have already reached the cloud.

### 🏛 3. The Compliance Risk (Briefly)
Sending unauthorized PII (like SSNs or emails in a test database) to foreign LLM APIs violates GDPR and DPDP regulations.

---

## 🟢 The Solution: Guardian Runtime

Guardian Runtime is a **local-first security middleware and FinOps firewall**. It runs entirely on your local machine and intercepts LLM traffic *before* it leaves your infrastructure. 

| The Problem | How Guardian Solves It |
| :--- | :--- |
| **Cost Runaways** | **Hard FinOps Budgets & Optimization:** Tracks every token you spend locally. You can set a strict "$5.00 per day" limit. Advanced **Terse Mode** aggressively optimizes input context and provides output brevity enforcement via system prompt injection. In benchmarks across real developer prompts, it reduces output tokens by 40–70% while maintaining full technical accuracy. |
| **Data Exfiltration** | **Zero-Latency Secret Scanners:** Scans every prompt for API keys, AWS credentials, and secrets *locally*. If it detects a secret, it instantly drops the request before it reaches the internet. |
| **Compliance** | **Local PII Blocking:** Regex and ML scanners prevent PII from leaving your machine. |

---

## 🏗 Architecture & The Security Pipeline

Guardian intercepts traffic at the network layer or via SDK, passing it through a strict verification pipeline before it ever reaches the cloud.

```text
  Agent / Dev                 Guardian Runtime                   Cloud LLM
       │                             │                               │
       │  1. Prompt + Context        │                               │
       │ ──────────────────────────▶ │                               │
       │                             │                               │
       │                             │ [Security Firewall]           │
       │                             │ ├─ Scan AWS Keys / Secrets    │
       │                             │ └─ Block if Threat Detected ──┼─ (Drops Request)
       │                             │                               │
       │                             │ [Token Optimizer]             │
       │                             │ ├─ Compress Whitespace        │
       │                             │ └─ Terse Mode (Output Trim)   │
       │                             │                               │
       │                             │ [FinOps Budget]               │
       │                             │ ├─ Check Daily Spend Limit    │
       │                             │ └─ Block if $5 Limit Hit ─────┼─ (Drops Request)
       │                             │                               │
       │                             │  2. Sanitized Prompt          │
       │                             │ ────────────────────────────▶ │
       │                             │                               │
       │                             │  3. LLM Response              │
       │                             │ ◀──────────────────────────── │
       │                             │                               │
       │                             │ [Output Guard]                │
       │                             │  Audit for Leaked PII/Secrets │
       │                             │                               │
       │  4. Safe Response           │                               │
       │ ◀────────────────────────── │                               │
       │                             │                               │
```

---

## 🔌 Supported Integrations

Guardian Runtime acts as an HTTP proxy or a native Python SDK, meaning it integrates effortlessly with almost any modern AI tool without modifying their internal code.

- **Visual IDEs:** Cursor, Windsurf, VS Code (via Cline/RooCode)
- **Terminal Agents:** Claude Code, Aider, GitHub Copilot CLI
- **Frameworks:** LangChain, AutoGen, LlamaIndex, CrewAI
- **LLM Providers:** OpenAI, Anthropic, Google Gemini (via OpenAI compatibility layer)
- **Supported Models:** Claude Fable 5, Claude Opus 4.8, GPT-5.5, Gemini 3.5

---

## 🚀 Quickstart & Installation

```bash
# Core framework only
pip install guardian_runtime

# Or install with specific LLM providers:
pip install "guardian_runtime[openai]"
pip install "guardian_runtime[anthropic]"
pip install "guardian_runtime[gemini]"

# Or install everything (Providers, ML Scanner, Document Converter):
pip install "guardian_runtime[all]"
```
*Done. No signup, no keys, zero configuration required. All monitoring data stays on your local machine in `~/.guardian_runtime/`.*

---

## 🎯 Comprehensive Use Cases (Where & How to Use)

Guardian is designed to be universal. Here are the exact ways to deploy it based on your workflow.

### 1. Terminal Coding Agents (Claude Code, Aider)
**Why use it here?** CLI agents operate autonomously. They can accidentally read a `.env` file containing your production AWS keys and send it to Anthropic/OpenAI as context. Guardian prevents this and ensures the agent doesn't blow your budget.

**How to use:**
1. Start the proxy in a background terminal:
   ```bash
   guardian_runtime proxy --port 8080
   ```
2. Tell your agent to route traffic through the proxy using environment variables:
   *In PowerShell:*
   ```powershell
   $env:ANTHROPIC_BASE_URL="http://localhost:8080"
   claude
   ```
   *In Mac/Linux/Git Bash:*
   ```bash
   export ANTHROPIC_BASE_URL=http://localhost:8080
   claude
   ```

### 2. Visual IDEs (Cursor, Windsurf)
**Why use it here?** Modern GUI editors like Cursor have deep codebase access. While coding, you might highlight a file containing a secret and ask "explain this file". Guardian stops Cursor from sending that secret to the cloud.

**How to use (Cursor Example):**
1. Start the proxy in your terminal: `guardian_runtime proxy --port 8080`
2. Open Cursor Settings (`Cmd/Ctrl + ,`)
3. Navigate to **Models > Override Base URL**
4. Set the Base URL to: `http://localhost:8080`
*(Now all of Cursor's traffic is protected and tracked locally!)*

### 3. Production Python Applications (SDK)
**Why use it here?** If you are building a production chatbot or RAG pipeline, you must ensure your users cannot perform "jailbreak" prompt injections or trick the LLM into leaking internal system prompts.

**How to use:**
Use Guardian as a drop-in replacement for the OpenAI/Anthropic SDK.
```python
import os
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

os.environ["OPENAI_API_KEY"] = "sk-proj-..."
gr = GuardianRuntime() # Zero-config initialization

try:
    # Protects user input before sending to OpenAI
    response = gr.complete(
        messages=[{"role": "user", "content": "My AWS Key is AKIAIOSFODNN7EXAMPLE"}],
        raise_on_block=True
    )
    print(response.content)
except GuardianRuntimeBlockedError as e:
    # Fails cleanly in your app instead of leaking the secret!
    print(f"Blocked Locally: {e.response.violations[0].detail}")
```

### 4. Agentic Frameworks (LangChain, AutoGen)
**Why use it here?** Frameworks that spawn multiple communicating agents can rapidly consume tokens. Guardian acts as a central cost-tracking hub for all agent nodes.

**How to use:**
Point your framework's `base_url` to the local proxy.
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="http://localhost:8080", # Traffic routes through Guardian
    api_key="sk-proj-..."
)
response = llm.invoke("Hello, Guardian!")
```

### 5. Data Prep for Web UIs (Document Conversion)
**Why use it here?** If you use the standard ChatGPT or Claude Web UI, uploading large PDFs eats up your context window quickly because PDFs contain massive amounts of hidden formatting bloat. 

**How to use:**
Use the built-in CLI to strip out formatting bloat and compress documents into pure Markdown *before* manually uploading them.
```bash
guardian_runtime convert <path/to/input.pdf> --out <path/to/output.md>
```
*You can now upload `cleaned_report.md` to ChatGPT, saving huge amounts of context space and preventing hallucination.*

---

## 💻 Exhaustive CLI Command Reference

Guardian ships with a powerful suite of offline CLI tools. All data is stored purely locally in `~/.guardian_runtime/`. 
Below is a detailed dive into every command, its flags, and exactly how and why to use it.

### `guardian_runtime proxy` (The Security Firewall)
Starts the local HTTP interception server. This is the core engine for protecting tools that you cannot edit the source code for (like Cursor or Claude Code).

**Flags & Options:**
- `--port, -p <int>`: Port to listen on (Default: `8080`).
- `--host <str>`: Host to bind to. Use `0.0.0.0` to expose on your local network (Default: `127.0.0.1`).
- `--policy <path>`: Path to a custom `policy.yaml` file. If omitted, uses the default Zero-Config policy ($10 budget).
- `--reload`: Enables auto-reload if the policy file changes (useful for dev mode).

**Example Usage:**
```bash
$ guardian_runtime proxy --port 8080
  ⛨  GuardianRuntime Runtime Proxy
  ─────────────────────────────────────────
  Listening on : http://127.0.0.1:8080
  Policy       : Default (Zero-Config)
  Dashboard    : guardian_runtime dashboard (run in another terminal)

  Agent setup:
    Claude Code  →  ANTHROPIC_BASE_URL=http://localhost:8080 claude
    Aider        →  OPENAI_BASE_URL=http://localhost:8080 aider
    Cursor       →  Settings → API Base → http://localhost:8080
```

### `guardian_runtime convert <path>` (Document Analysis)
Converts massive PDF, DOCX, and XLSX files into highly compressed, token-optimized Markdown. 

**Why use this?** If you upload a raw PDF to a Web UI (like ChatGPT) or parse it in an agent, you waste thousands of tokens on hidden formatting bloat. This command strips the bloat *before* it hits the LLM context window.

**Arguments & Flags:**
- `<path>`: The absolute or relative path to the document you want to compress.
- `--out, -o <path>`: Output file path for the converted Markdown. If omitted, prints a preview to the terminal.

**Example Usage:**
```bash
$ guardian_runtime convert <path/to/input_file> --out <path/to/output_file.md>
⛨ GuardianRuntime Document Converter
Processing: input_file...

✓ Conversion Complete!
  • Original File:  input_file
  • Token Count:    14,205
  • Saved to:       output_file.md
```

### `guardian_runtime scan <text>` (Manual Threat Verification)
Performs a local security scan on a specific text string using the ML InputGuard and Regex scanners.

**Why use this?** Use this to verify exactly what the firewall will catch before you send a massive codebase to an agent, or if you want to test how sensitive the PII/Secret detection is.

**Example Usage:**
```bash
$ guardian_runtime scan "My AWS key is AKIAIOSFODNN7EXAMPLE"
🛑 Scan failed! Threats detected:
  - [HIGH] secret_detected: AWS Access Key ID found.
```

### `guardian_runtime analytics` (FinOps Tracking)
Prints a beautiful terminal summary of today's API costs, token usage, and intercepted threats broken down by tool.

**Flags:**
- `--all`: Shows all-time historical analytics instead of just today.

**Example Usage:**
```bash
$ guardian_runtime analytics
  ⛨  GuardianRuntime Session Analytics (Today)
  ──────────────────────────────────────────────

  Claude Code
  Cost:       $2.3100
  Requests:   54
  Blocked:    3 (3 secret_detected)
  Tokens:     82,000
```

### Additional Administration Commands
- **`guardian_runtime --help`**: Prints the global help menu listing all available commands and flags.
- **`guardian_runtime dashboard`**: Launches a beautiful React-based local Web UI tracking costs and threats on port 3000. It visualizes the analytics data with charts.
- **`guardian_runtime logs`**: Tails the local JSONL event stream in real-time (`tail -f ~/.guardian_runtime/logs/events.jsonl`). Perfect for debugging exactly why a specific prompt was blocked.
- **`guardian_runtime init`**: Generates a boilerplate `policy.yaml` file in your current directory. Use this if you want to customize budgets, disable ML scanners, or enforce strict enterprise PII blocking.
- **`guardian_runtime validate`**: Checks your `policy.yaml` for syntax errors before you restart the proxy.
- **`guardian_runtime status`**: Shows the health of the local installation, ML models, and storage directory.
- **`guardian_runtime clean`**: Deletes your entire `~/.guardian_runtime` directory. Use this if you want to permanently delete all local analytics, logs, and custom policies.

---

## ⚙️ Advanced Configuration (Policy YAML)

Guardian Runtime is perfectly tuned out of the box with a $10 daily budget and strict secret scanning. If you need custom rules, run `guardian_runtime init` to create a `policy.yaml`:

```yaml
version: "1.0"
agents:
  default:
    llm:
      provider: openai
      default_model: gpt-4o

    input_guard:
      scanner_enabled: true
      jailbreak_detection: true
      scanner_action: block 
      
    cost:
      daily_budget: 5.00        # Instantly block if daily spend exceeds $5.00
      max_input_tokens: 20000   # Block massive context windows to save money
      
    optimizer:
      enabled: true
      terse_mode: true          # Slashes output tokens by forcing terse shorthand
```

---

## 🛑 What happens when Guardian blocks a request?

**Where will I see the block?**
* **If using the Proxy:** You will see the block in the terminal running `guardian_runtime proxy`, AND inside the UI of the tool you are using (e.g., Claude Code or Aider).
* **If using the Python SDK:** It surfaces instantly in your standard Python server logs or terminal.

**How is it blocked?**
* **Proxy Mode:** Guardian returns a graceful error with a clear message. This ensures CLI agents display a clean error message in their chat interface instead of crashing or freezing your session.
* **SDK Mode:** Guardian raises a `GuardianRuntimeBlockedError` exception that can be cleanly caught.

**Example Block Message:**
`BadRequestError: 🚨 [SECRET_DETECTED] AWS key AKIAIOS... found. Request blocked locally.`

---

## 📜 License

Released under the **MIT License**. <br/>Zero tracking, zero cloud dependencies. Your code is yours.
