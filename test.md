GUARDIAN-RUNTIME

* [ABOUT](#why-guardian)
* [HOW IT WORKS](#pipeline)
* [FEATURES](#features)
* [QUICKSTART](#quickstart)
* [INTEGRATIONS](#integration)

[☕ BUY
ME A COFFEE](https://buymeacoffee.com/ashishp05)
[⬡ GITHUB](https://github.com/ashp15205/guardian-runtime)

SYSTEM ONLINE

FREE & OPEN SOURCE

v1.0.10

USERS: 0

[★ GITHUB STARS: ...](https://github.com/ashp15205/guardian-runtime)

⬡ LOCAL-FIRST · ZERO DATA EXPOSURE · OPEN SOURCE

# GUARDIAN RUNTIME

A Python SDK that sits between your AI app and any LLM
**intercepting every prompt and response** to enforce security policies,
block data leaks, and detect threats.
**Everything runs locally.**

[⭐ GITHUB REPO](https://github.com/ashp15205/guardian-runtime)
[pip install guardian-runtime](https://pypi.org/project/guardian-runtime/)
[VIEW QUICKSTART](#quickstart)

$ pip install "guardian-runtime[all]"

✓ Successfully installed guardian-runtime-1.0.9 with ML Scanners & Providers

$ guardian\_runtime proxy --port 8080

✓ Proxy started on port 8080. Zero-Config Mode Active.

# Claude Code tries to send an .env file...

🚨 [SECRET\_DETECTED] AWS key AKIAIOSFODNN7EXAMPLE found — BLOCKED

# Agent gets stuck in an infinite loop...

🚨 [BUDGET\_EXCEEDED] Daily budget of $10.00 exceeded. Current spend: $10.05 —
BLOCKED

$

// THE WHY, WHAT & HOW

## THE PROBLEM & THE SOLUTION

THE PROBLEM

### Developers Are Flying Blind

**1. The Cost Risk:** CLI coding agents (Claude Code, Cursor, Aider) run autonomously.
If they get stuck in an infinite retry loop or parse a massive log file, you wake up to a
**$50 API bill**. You have zero visibility into session costs until the bill arrives.

**2. The Security Risk:** Coding agents have full access to your workspace. If you
accidentally leave an `AWS_SECRET_KEY` or `.env` credential in a file, the
agent will silently upload it to a third-party LLM provider.

THE SOLUTION

### A Developer-First Local Firewall

Guardian Runtime is a zero-latency FinOps and Security firewall. It runs entirely on your local
machine and sits directly between your coding agents and the LLM provider.

**Session Analytics & Hard Budgets:** Automatically tracks tokens and costs per session
via the CLI. It sets a hard $10/day default limit so infinite loops never drain your credit card.

**Local Secret Scanning:** Instantly intercepts and blocks API keys, AWS credentials,
and `.env` secrets from ever leaving your local machine. Zero configuration required.

// ARCHITECTURE

## THE SECURITY PIPELINE

👤

SOURCE

User Input

──▶

🛡

FIREWALL

Secret Guard

──▶

⚙

OPTIMIZER

Token Trim

──▶

🤖

TARGET

LLM API

──▶

💰

FINOPS

Budget Enforcer

──▶

✅

CLEAN

Safe Response

EVERY PROMPT IS SCANNED BEFORE IT LEAVES YOUR MACHINE.
EVERY RESPONSE IS VALIDATED BEFORE IT REACHES YOUR USER.
ZERO DATA LEAVES YOUR INFRASTRUCTURE.

// CAPABILITIES

## PLATFORM FEATURES

01

💰

Hard Local Budgets

Configure a strict daily budget so runaway agents or infinite loops can't
drain your API credits. Stops the bleeding instantly with zero cloud dependency.

FinOps
Cost Control

02

🔑

ML-Powered Secret Firewall

Uses Microsoft Presidio for high-accuracy NLP scanning (emails, phones) and
rigorous Regex fallbacks for API keys. Blocks threats locally.

PRESIDIO
REGEX
ZERO-LATENCY

03

📉

Token Optimizer

Automatically trims redundant tokens, conversational filler, and excessive
whitespace from prompts before they hit the LLM. Passively saves you money on every request.

Token Reduction
Auto-Savings

04

🌐

Universal Local Proxy

A built-in proxy server lets you intercept traffic from CLI agents (Claude
Code, Aider) without modifying their source code. Perfect for solo developers or internal tools.

Claude Code
Aider
LangChain

05

🏴‍☠️

Jailbreak & Unsafe Command Defense

Pattern-matched detection for DAN variants, instruction overrides, and system
prompt extraction attempts. Stops adversarial prompts from hijacking your agent.

DAN
Injection

06

📊

Session Analytics Dashboard

Automatically tracks tokens, costs, and blocked requests for all your CLI
tools in real-time. Instantly view your exact daily spend with the `analytics` command.

Visibility
CLI Metrics

// DEPLOY IN MINUTES

## QUICKSTART

01

Install

Zero external dependencies for core detection. Optional extras for proxy and
dashboard.

pip install "guardian-runtime[all]"

02

Wrap your LLM call

Drop Guardian between your app and any LLM. One import, one object, fully
governed calls.

from guardian\_runtime import
GuardianRuntime

gr = GuardianRuntime()

# Your normal LLM call — now governed

response = gr.complete(

  model="gpt-4o",

  messages=[{"role": "user", "content": user\_input}]

)

# response.blocked → True if threat detected

# response.violations → list of what was caught

# response.estimated\_cost\_usd → spend this call

03

Configure your policy (optional)

Guardian works zero-config out of the box. But if you want to enforce strict
budgets or enterprise PII blocking, create a `policy.yaml` file.

version: "1.0"

agents:

  default:

    cost:

      daily\_budget: 10.00 # Strict daily budget limit in USD ($)

      max\_input\_tokens: 50000

    input\_guard:

      pii\_detection: true # Opt-in for enterprise SSN/Credit Card blocking

04

Use the CLI Tools

Guardian comes with built-in terminal tools for management and local logging.

# Initialize local log directories (~/.guardian\_runtime/logs)
guardian\_runtime init

# View Session Analytics (Cost & Tokens per CLI tool)
guardian\_runtime analytics

# Tail live security threat logs
guardian\_runtime logs --tail 20

# Start the local interception proxy
guardian\_runtime proxy --port 8080

// MECHANICS

## WHAT HAPPENS WHEN GUARDIAN BLOCKS?

### 01. WHERE WILL THEY SEE IT?

If using the **Proxy**, developers see the block instantly inside the UI of their tool
(e.g. Claude Code chat) *and* in the background proxy logs.

If using the **SDK**, it surfaces in their standard Python server logs.

### 02. HOW IS IT BLOCKED?

**Zero crashes.** In Proxy mode, Guardian cleanly returns a standard `HTTP 400/403`
error. This ensures CLI agents display an error message gracefully instead of crashing their
process.

In SDK mode, it raises a standard Python Exception.

### 03. WHAT DO THEY SEE?

No obscure stack traces. They see a completely transparent, actionable string telling them exactly
what policy they violated.

Example: 🚨 [BUDGET\_EXCEEDED] Daily budget of $10.00
exceeded.

// INTEGRATION GUIDES

## HOW TO USE GUARDIAN

01

Custom Python Apps (Chatbots, RAG)

If you are building your own AI application in Python, use the SDK
directly.

# 1. Install the package
pip install "guardian-runtime[all]"

# 2. In your code, wrap your LLM calls
from guardian\_runtime import GuardianRuntime
gr = GuardianRuntime.from\_policy("policy.yaml")

# Instead of calling OpenAI/Anthropic directly:
response = gr.complete(
  messages=[{"role": "user", "content": "My SSN is 123-45-6789"}]
)

$ python run\_chatbot.py

# Guardian intercepts before the network call:
Traceback (most recent call last):
  File "run\_chatbot.py", line 12, in <module>
GuardianRuntimeBlockedError: 🚨 [PII\_DETECTED] 1 Policy
Violations:
  - SSN number found in prompt. Severity: HIGH.

02

Developers (Claude Code or Aider Users)

Stop CLI agents from getting stuck in loops and blowing your API budget.
Guardian's zero-config local proxy sits between your agent and Anthropic/OpenAI.

# 1. Install Guardian and start the Proxy
pip install "guardian-runtime[all]"
guardian\_runtime proxy --port 8080

# 2. Tell Claude to use the proxy
export ANTHROPIC\_BASE\_URL=http://localhost:8080
claude

# Claude attempts to read an .env file to fix a bug...

Claude> I will check your .env file for the AWS
credentials.
Reading .env...
Sending context to Anthropic...

# Guardian Proxy blocks the HTTP request instantly:
Error: HTTP 403 Forbidden. 🚨 [SECRET\_DETECTED] AWS key AKIAIOSFODNN7EXAMPLE
found.

03

Visual IDEs (Cursor, Windsurf)

GUI editors have deep codebase access. Guardian stops them from sending highlighted secrets to the cloud.

# 1. Start the Proxy in your terminal
guardian\_runtime proxy --port 8080

# 2. In Cursor Settings (Cmd+,)
Navigate to **Models > Override Base URL**
Set it to: http://localhost:8080

# You ask Cursor to explain an AWS config file...

Cursor> Explain the code in config.json
Reading config.json...

# Guardian Proxy blocks it locally before it hits the internet:
Error: HTTP 403 Forbidden. 🚨 [SECRET\_DETECTED] AWS key found.

04

Enterprise Teams (LangChain, AutoGen)

Working at a company? Use Guardian to enforce strict policies across all
internal AI tools so your employees don't accidentally leak customer PII or proprietary code.

# Wrap any LangChain or AutoGen client
from langchain\_openai import ChatOpenAI

# Point your framework to the local proxy:
llm = ChatOpenAI(
  model="gpt-4o",
  base\_url="http://localhost:8080"
)
chain.invoke({"input": user\_query})

# LangChain Trace:
[chain/start] [1:chain:AgentExecutor] Entering Chain run
[llm/start] [1:chain:AgentExecutor > 2:llm:ChatOpenAI] Entering LLM
run

[llm/error] [1:chain:AgentExecutor > 2:llm:ChatOpenAI] [0ms] LLM run
errored
BadRequestError: Error code: 400 - {'error': {'message': '🚨
[BUDGET\_EXCEEDED] Daily budget of $50.00 exceeded.', 'type': 'policy\_violation'}}

05

Document Converter (Zero-Code)

If you process large PDFs or Word documents for RAG, they often contain
massive amounts of formatting bloat. Use the built-in CLI to instantly clean and convert them
into pure Markdown.

# Simply pass any PDF or DOCX file to the CLI:
guardian\_runtime convert financial\_report.pdf \
  --out clean\_report.md

$ guardian\_runtime convert financial\_report.pdf
--out clean\_report.md

⛨ GuardianRuntime Document
Converter
Processing: financial\_report.pdf...

✓ Conversion Complete!
  • Original File: financial\_report.pdf
  • Token Count: 14,205
  • Saved to: clean\_report.md

06

Session Analytics (FinOps)

Guardian automatically tracks your spend across every CLI tool and script you
use. Never wonder how much a Claude Code refactor cost you again.

# At the end of the day, just run:
guardian\_runtime analytics

# Or see all-time history:
guardian\_runtime analytics --all

$ guardian\_runtime analytics

⛨ GuardianRuntime Session
Analytics (Today)
──────────────────────────────────────────────

Claude Code
Cost: $2.3100
Requests: 54
Blocked: 3 (3
secret\_detected)
Tokens: 82,000

// COMMAND LINE INTERFACE

## EXHAUSTIVE CAPABILITIES & CLI

guardian\_runtime proxy

The Security Firewall

Starts the local HTTP interception server. This is the core engine for protecting tools that you cannot edit the source code for (like Cursor or Claude Code).

FLAGS:
--port, -p <int> (Default: 8080)
--host <str> (Default: 127.0.0.1)
--policy <path> (Custom policy.yaml)
--reload (Dev mode)

$ guardian\_runtime proxy --port 8080

⛨ GuardianRuntime Runtime Proxy
─────────────────────────────────────────
Listening on : http://127.0.0.1:8080
Policy : Default (Zero-Config)

guardian\_runtime convert <path>

Document Analysis & Compression

Converts massive PDF, DOCX, and XLSX files into highly compressed, token-optimized Markdown to prevent wasting tokens on hidden formatting bloat in RAG pipelines.

ARGS/FLAGS:
<path> (Input file path)
--out, -o <path> (Output file path)

$ guardian\_runtime convert report.pdf -o clean.md

✓ Conversion Complete!
 • Original File: report.pdf
 • Token Count: 14,205
 • Saved to: clean.md

guardian\_runtime scan <text>

Manual Threat Verification

Performs a local security scan on a specific text string using the ML InputGuard. Use this to verify exactly what the firewall will catch before sending a payload.

$ guardian\_runtime scan "Key is AKIAIOSF..."

🛑 Scan failed! Threats detected:
 - [HIGH] secret\_detected: AWS Access Key ID

guardian\_runtime analytics

FinOps Cost Tracking

Prints a beautiful terminal summary of API costs, token usage, and intercepted threats broken down by tool.

FLAGS:
--all (Show all-time historical data)

$ guardian\_runtime analytics

Claude Code
Cost: $2.3100
Blocked: 3 (secret\_detected)

Additional Administration Commands

guardian\_runtime dashboard

Launches a React-based local Web UI tracking costs and threats on port 3000.

guardian\_runtime logs

Tails the local JSONL event stream (`tail -f ~/.guardian\_runtime/logs/events.jsonl`). Perfect for debugging exact block reasons.

guardian\_runtime init

Generates a boilerplate policy.yaml file for customizing budgets or ML scanners.

guardian\_runtime validate

Checks your policy.yaml for syntax errors before you restart the proxy.

guardian\_runtime status

Shows the health of the local installation.

DEPLOY IN 60 SECONDS

// FREE · OPEN SOURCE · LOCAL-FIRST · MIT LICENSE

[⬡ GITHUB REPO](https://github.com/ashp15205/guardian-runtime)
[READ THE DOCS](#quickstart)

© 2026 GUARDIAN RUNTIME — MIT LICENSE

[☕ Buy Me A Coffee](https://buymeacoffee.com/ashishp05)
[📦 PyPI](https://pypi.org/project/guardian-runtime/)
[⭐ GitHub](https://github.com/ashp15205/guardian-runtime)