<p align="center">
  <img src="https://img.shields.io/badge/GuardianRuntime-Local%20AI%20Firewall-00ff88?style=for-the-badge&logo=shield&logoColor=black" alt="GuardianRuntime" />
</p>

<h1 align="center">Guardian Runtime</h1>

<p align="center">
  <strong>A Zero-Latency FinOps & Security Firewall for AI Applications.<br>
  Intercept every prompt and response locally. Stop data leaks and runaway token costs.</strong>
</p>

<p align="center">
  🌐 <strong>Website & Docs:</strong> <a href="https://ashp15205.github.io/guardian-runtime/">https://ashp15205.github.io/guardian-runtime/</a><br>
  📦 <strong>Available on PyPI:</strong> <a href="https://pypi.org/project/guardian-runtime/">https://pypi.org/project/guardian-runtime/</a>
</p>
<p align="center">
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/v/guardian-runtime.svg?style=flat-square&color=00ff88" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/guardian-runtime/"><img src="https://img.shields.io/pypi/pyversions/guardian-runtime.svg?style=flat-square" alt="Python Versions"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/no%20signup-no%20key-00ff88?style=flat-square" alt="No signup required">
  <img src="https://img.shields.io/badge/100%25-local%20execution-00ff88?style=flat-square" alt="100% Local">
</p>

---

## 🛑 The Problem: Data Privacy Black Boxes & Runaway Costs

Developers are building incredible AI applications, but they are often blindly passing raw user data to external APIs. If a user pastes a **credit card** into a chat, or a developer accidentally leaves an **AWS Key** in an agent prompt, that data is instantly transmitted and logged in a cloud provider's database. Furthermore, malicious users can inject **Jailbreaks** to hijack your AI.

Worse yet, unrestricted employee access to AI tools is causing massive budgeting crises. **Companies are blowing through their annual LLM token budgets in mere months** due to developers sending unoptimized, massive context windows and infinite loops to expensive models without oversight.

## 🟢 The Solution: A Zero-Latency FinOps Firewall

**Guardian Runtime** acts as an invisible shield sitting directly on your own infrastructure. Before a single byte of data leaves your network to reach OpenAI or Anthropic, Guardian scans, cleans, and optimizes it locally.

- **Data Security**: It uses lightning-fast pattern matching to block PII, secrets, and jailbreaks in milliseconds.
- **Cost Control**: The built-in Token Optimizer actively strips redundant whitespace and bloat from prompts.
- **FinOps Limits**: Strict FinOps rules instantly block requests that exceed your maximum token budgets—stopping runaway spend in its tracks.

Everything happens locally on your CPU. It costs zero API fees and takes less than 5 milliseconds.

---

## ⚡ Key Features

1. **🔒 PII & Data Leak Prevention**: Detects and blocks Aadhaar, PAN, SSNs, credit cards, emails, and phone numbers using local regex and NLP.
2. **🔑 Secret & Credential Scanning**: Catches hardcoded API keys (AWS, OpenAI, GitHub) before they ever leave your machine.
3. **💰 Token Optimizer & FinOps**: Compresses redundant whitespace and enforces maximum token budgets per request.
4. **🏴‍☠️ Jailbreak Defense**: Defends against 50+ known adversarial prompt patterns (e.g., "Ignore previous instructions", DAN payloads).
5. **🌐 Universal Proxy**: Works seamlessly with LangChain, Cursor IDE, Anthropic Claude Code, and any OpenAI-compatible client.
6. **📊 Local Dashboard & Audit Logs**: Tracks every intercepted threat and token cost locally in `~/.guardian_runtime/logs/` with a beautiful built-in web dashboard.

---

## 🏗 Architecture

```text
       👤 USER INPUT / APP LOGIC
                 │
                 ▼
 ┌──────────────────────────────────────┐
 │ 🛡 GUARDIAN RUNTIME (Local Proxy)     │
 │                                      │
 │  1. Input Guard (PII/Secrets)        │ ──(Blocks Threats)
 │  2. Token Optimizer                  │ ──(Reduces Cost)
 │  3. FinOps Limits                    │ ──(Enforces Budgets)
 └───────────────┬──────────────────────┘
                 │ (Cleaned & Optimized)
                 ▼
      ☁️ LLM API (OpenAI/Anthropic)
                 │
                 ▼
 ┌──────────────────────────────────────┐
 │ 🛡 GUARDIAN RUNTIME (Local Proxy)     │
 │                                      │
 │  1. Output Guard (Auditor)           │ ──(Flags Leaks/PII)
 └───────────────┬──────────────────────┘
                 │ (Safe Response)
                 ▼
           💻 USER SCREEN
```

---

## 🚀 Quickstart

### Installation

```bash
pip install guardian-runtime
guardian_runtime init
```

### Integration Methods

Guardian can be used as a drop-in **Python SDK** or as a **Local HTTP Proxy** for tools you can't edit.

#### Case 1: Custom Python Application (SDK)
Replace your direct LLM calls with the `GuardianRuntime` wrapper.

```python
import os
from guardian_runtime import GuardianRuntime, GuardianRuntimeBlockedError

os.environ["OPENAI_API_KEY"] = "sk-proj-..."

# Loads FinOps and Security rules from policy.yaml
gr = GuardianRuntime.from_policy("policy.yaml")

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

#### Case 3: Cursor IDE
Prevent accidental leaks of proprietary company secrets when using Cursor's AI Chat and Composer.

1. Start the proxy: `guardian_runtime proxy --port 8080`
2. Open Cursor Settings (Cmd+,)
3. Go to **Models > Override Base URL**
4. Set it to: `http://localhost:8080`

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

## ⚙️ Configuration (`policy.yaml`)

Define your security thresholds and budget rules without touching your code.

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
      pii_detection: true
      jailbreak_detection: true
      pii_action: block 

    optimizer:
      enabled: true
      whitespace_normalization: true
      
    cost:
      max_input_tokens: 50000   # Instantly blocks massive context windows
      max_output_tokens: 4000
```

---

## 🔍 Output Auditing (Non-Blocking)

By default, the **Input Guard** acts as a strict firewall—blocking requests containing secrets or PII before they cost you money. 

The **Output Guard**, however, acts as an **Auditor**. If an LLM accidentally hallucinates an internal API key or PII in its response, Guardian will *not* drop the response. Instead, it passes the message back to your application but attaches a list of `violations` to the response object. This allows your application to handle the mistake gracefully on the frontend.

---

## 📈 CLI Tools & Dashboard

Guardian ships with built-in tools for local observability. All logs are stored strictly on your local machine in `~/.guardian_runtime/logs/`.

```bash
# View live intercepted traffic
guardian_runtime logs --tail 20

# Check total session cost
guardian_runtime status

# Launch the local FinOps & Security dashboard
guardian_runtime dashboard
```

---

## 📜 License

Released under the **MIT License** — free to use, modify, and distribute. Zero tracking, zero cloud dependencies.
