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

## 📖 Table of Contents
- [🛑 The Problem: Developers are Flying Blind](#-the-problem-developers-are-flying-blind)
- [🟢 The Solution: A Developer-First Local Firewall](#-the-solution-a-developer-first-local-firewall)
- [⚡ Key Features](#-key-features)
- [🏗 Architecture](#-architecture)
- [🚀 Quickstart](#-quickstart)
- [🛑 What happens when Guardian blocks a request?](#-what-happens-when-guardian-blocks-a-request)
- [⚙️ Advanced Configuration (Optional)](#️-advanced-configuration-optional)
- [🔍 Output Auditing (Non-Blocking)](#-output-auditing-non-blocking)
- [📈 CLI Tools & Dashboard](#-cli-tools--dashboard)
- [📜 License](#-license)

---

## 🛑 The Problem: Developers are Flying Blind

1. **The Cost Risk:** CLI coding agents (Claude Code, Cursor, Aider) run autonomously. If they get stuck in an infinite retry loop or parse a massive log file, you wake up to a **$50 API bill**. You have zero visibility into session costs until the bill arrives.
2. **The Security Risk:** Coding agents have full access to your workspace. If you accidentally leave an `AWS_SECRET_KEY` or `.env` credential in a file, the agent will silently upload it to a third-party LLM provider.

## 🟢 The Solution: A Developer-First Local Firewall

- **ML-Powered PII & Secret Scanning**: Uses Microsoft Presidio for high-accuracy NLP scanning (emails, phones, SSNs) and rigorous Regex fallbacks for secrets (AWS keys, OpenAI keys). Runs 100% locally with zero latency.
- **Jailbreak Detection**: Pre-emptively blocks DAN prompts and instruction-override injections.
- **High-Concurrency Threadpool Proxy**: The local proxy seamlessly handles hundreds of simultaneous requests with zero event-loop blocking, making it perfect for multi-agent terminal systems.
- **Graceful Upstream Error Handling**: Mid-stream LLM API outages are handled beautifully, keeping your terminal bots alive instead of crashing them with 500 errors.
- **Session Analytics & Hard Budgets**: Automatically tracks tokens and costs per session via the CLI. It sets a hard $10/day default limit so infinite loops never drain your credit card.
- **Local Secret Scanning**: Instantly intercepts and blocks API keys, AWS credentials, and `.env` secrets from ever leaving your local machine.
- **Zero Config**: No complex policies required. It protects your budget and secrets out of the box.

---

## ⚡ Key Features

1. **💰 Custom Hard Budgets**: Configure a strict daily budget so runaway agents can't drain your API credits.
2. **🔑 Secret & Credential Firewall**: Catches hardcoded API keys (AWS, Stripe, OpenAI, GitHub) before they leave your laptop. 
3. **📉 Token Optimizer**: Compresses redundant whitespace and reduces prompt bloat to passively save you money.
4. **🌐 Universal Local Proxy**: Works seamlessly with CLI agents like Anthropic Claude Code and Aider.
5. **🏴‍☠️ Unsafe Command Defense**: Stops adversarial prompts from hijacking your agent to run malicious CLI commands.
6. **📊 Built-in Local Dashboard**: Tracks every intercepted threat and every cent spent locally in `~/.guardian_runtime/logs/` with a beautiful offline dashboard.

---

## 🏗 Architecture

```text
       👤 USER INPUT / APP LOGIC
                 │
                 ▼
 ┌──────────────────────────────────────┐
 │   GUARDIAN RUNTIME (Local Proxy)     │
 │                                      │
 │  1. Input Guard (Secret Scanner)     │ ──(Blocks Threats)
 │  2. Token Optimizer                  │ ──(Reduces Cost)
 │  3. FinOps Limits                    │ ──(Enforces Budgets)
 └───────────────┬──────────────────────┘
                 │ (Cleaned & Optimized)
                 ▼
      ☁️ LLM API (OpenAI/Anthropic)
                 │
                 ▼
 ┌──────────────────────────────────────┐
 │  GUARDIAN RUNTIME (Local Proxy)      │
 │                                      │
 │  1. Output Guard (Auditor)           │ ──(Flags Secrets)
 └───────────────┬──────────────────────┘
                 │ (Safe Response)
                 ▼
           💻 USER SCREEN
```

---

## 🚀 Quickstart

### Installation

```bash
# Core framework only
pip install guardian-runtime

# Or install with specific LLM providers:
pip install "guardian-runtime[openai]"
pip install "guardian-runtime[anthropic]"
pip install "guardian-runtime[google]"

# Or install everything (Providers, PII ML Scanner, Doc Converter):
pip install "guardian-runtime[all]"
```
Done. No signup, no keys, zero configuration required.

### Integration Methods

Guardian can be used as a drop-in **Python SDK** or as a **Local HTTP Proxy** for tools you can't edit.

#### Case 1: Custom Python Application (SDK)
Replace your direct LLM calls with the `GuardianRuntime` wrapper. Works instantly with zero configuration.

```python
import os
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

os.environ["OPENAI_API_KEY"] = "sk-proj-..."

# Zero-config initialization
gr = GuardianRuntime()

try:
    response = gr.complete(
        messages=[{"role": "user", "content": "My AWS Key is AKIAIOSFODNN7EXAMPLE"}],
        raise_on_block=True
    )
    print(response.content)
except GuardianRuntimeBlockedError as e:
    print(f"Blocked Locally: {e.response.violations[0].detail}")
```

#### Case 2: Claude Code & CLI Assistants
For CLI tools like Anthropic's Claude Code, start the proxy and override the base URL.

```bash
# 1. Start the proxy in a background terminal
guardian_runtime proxy --port 8080

# 2. Tell Claude to route traffic through Guardian
export ANTHROPIC_BASE_URL=http://localhost:8080
claude
```

#### Case 3: Cursor IDE (Coming Soon)
We are actively working on full support for Cursor's AI Chat and Composer.

1. Start the proxy: `guardian_runtime proxy --port 8080`
2. Open Cursor Settings (Cmd+,)
3. Go to **Models > Override Base URL**
4. Set it to: `http://localhost:8080` *(Note: May exhibit unstable behavior in current version)*

#### Case 4: Agentic Frameworks (LangChain / AutoGen)
Building autonomous agents? Guardian acts as a security middleware for any standard LLM client.

```python
from langchain_openai import ChatOpenAI

# Point LangChain to the Guardian Proxy
llm = ChatOpenAI(
    model="gpt-4o",
    base_url="http://localhost:8080"
)
```

#### Case 5: Document Analysis (RAG)
Heavy PDFs contain massive amounts of formatting bloat. Use the Document Converter to clean and compress them before the LLM sees them.

```python
from guardian_runtime import convert_document

doc = convert_document("financial_report.pdf")
print(doc.token_count) # See exactly how much context it uses
print(doc.content)     # Feed pure Markdown to your RAG
```

---

## 🛑 What happens when Guardian blocks a request?

When Guardian detects a Secret or a Budget Violation, it halts the request immediately. 

**Where will I see the block?**
* **If using the Proxy:** You will see the block in the terminal running `guardian_runtime proxy`, AND inside the UI of the tool you are using (e.g., Claude Code or Aider).
* **If using the Python SDK:** It surfaces instantly in your standard Python server logs or terminal.

**How is it blocked?**
* **Proxy Mode:** Guardian returns a graceful `HTTP 400/403` error. This ensures CLI agents display a clean error message in their chat interface instead of crashing or freezing your session.
* **SDK Mode:** Guardian raises a `GuardianRuntimeBlockedError` exception that can be cleanly caught in a standard `try/except` block.

**What will I see?**
You will see a completely transparent, actionable error message. No obscure stack traces.
* Example (Budget): `BadRequestError: 🚨 [BUDGET_EXCEEDED] Daily budget of $10.00 exceeded.`
* Example (Secret): `Error: HTTP 403. 🚨 [SECRET_DETECTED] AWS key AKIAIOS... found.`

---

## ⚙️ Advanced Configuration (Optional)

Guardian Runtime works perfectly out of the box for independent developers. But if you want to customize strict budgets or scan for custom secrets, you can create an optional `policy.yaml`:

```bash
guardian_runtime init
```

```yaml
version: "1.0"
name: "production"
interactive_mode: off

agents:
  default:
    llm:
      provider: openai
      default_model: gpt-4o

    input_guard:
      scanner_enabled: true
      jailbreak_detection: true
      scanner_action: block 

    optimizer:
      enabled: true
      whitespace_normalization: true
      
    cost:
      daily_budget: 10.00       # Instantly blocks if daily spend exceeds $10.00
      max_input_tokens: 50000   # Instantly blocks massive context windows
      max_output_tokens: 4000
```

---

## 🔍 Output Auditing (Non-Blocking)

By default, the **Input Guard** acts as a strict firewall—blocking requests containing secrets before they cost you money. 

The **Output Guard**, however, acts as an **Auditor**. If an LLM accidentally hallucinates an internal API key in its response, Guardian will *not* drop the response. Instead, it passes the message back to your application but attaches a list of `violations` to the response object. This allows your application to handle the mistake gracefully on the frontend.

---

## 📈 CLI Tools & Dashboard

Guardian ships with built-in tools for local observability. All logs are stored strictly on your local machine in `~/.guardian_runtime/logs/`.

```bash
# View live intercepted traffic
guardian_runtime logs --tail 20

# View Session Analytics (Cost & Tokens per CLI tool)
guardian_runtime analytics

# Launch the full local FinOps & Security dashboard
guardian_runtime dashboard
```

**Example Analytics Output:**
```text
  ⛨  GuardianRuntime Session Analytics (Today)
  ──────────────────────────────────────────────

  Claude Code
  Cost:       $2.3100
  Requests:   54
  Blocked:    3 (3 secret_detected)
  Tokens:     82,000
```

---

## 📜 License

Released under the **MIT License** — free to use, modify, and distribute. Zero tracking, zero cloud dependencies.
