# Guardian Runtime Architecture

Guardian Runtime is a **local-first runtime governance layer** for AI applications. It operates entirely on your local machine to intercept, scan, optimize, and log LLM traffic before it hits external APIs (like OpenAI or Anthropic).

## Core Philosophy

1. **Zero Cloud Dependencies**: No external license servers, no SaaS dashboards, no telemetry. Everything runs on `localhost` and state is stored in `~/.guardian_runtime/`.
2. **Developer First**: Aimed at stopping runaway budgets ($10/day limits) and accidental secret leaks (AWS/OpenAI keys) for independent developers and internal tools.
3. **Transparent Proxying**: Can be used as a Python SDK wrapper or as an HTTP proxy server that mimics the OpenAI API, allowing it to govern tools like Claude Code and Aider without source code modifications.

---

## 1. High-Level Data Flow

```text
       👤 USER INPUT / APP LOGIC / CLI AGENT
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
          APP / CLI / DEVELOPER
```

---

## 2. Core Components

### 2.1 The Local Proxy (`guardian_runtime/proxy/server.py`)
A fast, lightweight FastAPI server that mimics the `/v1/chat/completions` endpoint of the OpenAI API.
- **Function**: Intercepts requests from local agents (Claude Code, Cursor).
- **Execution**: Deserializes the payload, pushes it through the `GuardianRuntimeEngine`, and streams the response back to the client.

### 2.2 The Engine (`guardian_runtime/core/engine.py`)
The central nervous system of the SDK.
- **Input Pipeline**: Runs the raw prompt through the `InputGuard` and `InputOptimizer`.
- **Execution Pipeline**: Checks the local budget via `LocalStorage`. If allowed, forwards the request to the upstream LLM provider (`openai_provider.py`, `anthropic_provider.py`).
- **Output Pipeline**: Runs the response through the `OutputGuard` and updates local analytics (cost/tokens consumed).

### 2.3 The Guards (`guardian_runtime/guards/`)
- **Input Guard (`input_guard.py`)**: Runs `PIIDetector` configured specifically for high-confidence Secret Scanning (AWS keys, OpenAI keys). Also runs `JailbreakDetector` to block malicious DAN prompts.
- **Output Guard (`output_guard.py`)**: An auditor that scans the LLM's response for accidentally hallucinated secrets, flagging them without dropping the connection.

### 2.4 FinOps & Storage (`guardian_runtime/core/storage.py`)
- **Cost Calculation (`cost_calculator.py`)**: Precisely calculates the cost of requests based on the model (e.g., `gpt-4o`, `claude-3-5-sonnet`) and the actual tokens consumed.
- **Local Storage**: Writes daily limits to `~/.guardian_runtime/usage.json` and granular session events to `~/.guardian_runtime/logs/history.jsonl`.
- **Budget Enforcement**: If the daily budget (default $10/day) is exceeded, the Engine raises a `GuardianRuntimeBlockedError` before any network call is made.

### 2.5 Analytics Dashboard (`guardian_runtime/dashboard/server.py`)
A standalone local web application that serves a dark-mode dashboard.
- **Function**: Reads the `.jsonl` files stored in the local storage directory and aggregates them in real-time.
- **Display**: Shows total spend, tokens consumed, blocked requests, and violation types.

---

## 3. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Core Framework** | Python 3.10+ | Native compatibility with ML ecosystem |
| **Proxy & Dashboard** | FastAPI + Uvicorn | High performance asynchronous HTTP serving |
| **Validation** | Pydantic v2 | Strict schema validation for configurations |
| **Tokenization** | Tiktoken | Exact token counts for OpenAI models |
| **CLI** | Click | Beautiful, easy-to-use terminal interfaces |
| **Document Parsing** | MarkItDown | Strips bloat from complex documents (PDFs/PPTs) |

---

## 4. Security & Privacy

- **Data Locality**: No prompts, responses, or analytics are ever sent to a central Guardian server. All state is maintained locally.
- **Network Boundaries**: The Secret Scanner operates locally using regex, preventing your API keys from being transmitted to third-party LLMs over the wire.
- **Opt-In Overrides**: All strict constraints (like the $10 budget) can be dynamically overridden by the developer via the local `policy.yaml`.
