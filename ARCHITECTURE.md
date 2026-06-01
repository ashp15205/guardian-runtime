# Guardian Runtime — Complete Technical Architecture

> This document is the **single source of truth** for every component, library, function, API endpoint, data model, and design decision in Guardian Runtime. Read this before writing a single line of code.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure (Full Tree)](#3-project-structure-full-tree)
4. [Component Breakdown](#4-component-breakdown)
   - 4.1 [CLI Layer](#41-cli-layer)
   - 4.2 [Core Engine](#42-core-engine)
   - 4.3 [Input Guard](#43-input-guard)
   - 4.4 [Output Guard](#44-output-guard)
   - 4.5 [FinOps Engine](#45-finops-engine)
   - 4.6 [Tool Governor](#46-tool-governor)
   - 4.7 [Policy Engine](#47-policy-engine)
   - 4.8 [Local Storage](#48-local-storage)
   - 4.9 [License Manager](#49-license-manager)
   - 4.10 [Logging System](#410-logging-system)
   - 4.11 [Integrations](#411-integrations)
5. [License Key Server (Backend)](#5-license-key-server-backend)
6. [Developer Portal (Frontend)](#6-developer-portal-frontend)
7. [Data Models](#7-data-models)
8. [Request Flow (End-to-End)](#8-request-flow-end-to-end)
9. [YAML Policy Schema](#9-yaml-policy-schema)
10. [Local File System Layout](#10-local-file-system-layout)
11. [Database Schema (Supabase)](#11-database-schema-supabase)
12. [API Endpoints](#12-api-endpoints)
13. [Testing Strategy](#13-testing-strategy)
14. [Security Model](#14-security-model)
15. [Dependency Map](#15-dependency-map)

---

## 1. System Overview

Guardian Runtime is split into **three independent deployable units**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  UNIT 1: Python SDK (guardian-runtime)                              │
│  ─────────────────────────────────                                  │
│  • Installed via: pip install guardian-runtime                       │
│  • Runs on: developer's machine (100% local)                        │
│  • Language: Python 3.9+                                            │
│  • Published to: PyPI                                               │
│  • Contains: guards, finops, policy engine, local logging, CLI      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  UNIT 2: License Key Server (API)                                   │
│  ─────────────────────────────────                                  │
│  • Deployed to: Vercel (serverless)                                 │
│  • Language: TypeScript (Next.js API routes)                        │
│  • Database: Supabase (Postgres)                                    │
│  • Purpose: Validate license keys, track usage counts,              │
│             generate keys on payment                                │
│  • Receives from SDK: license_key + check_count (ONLY)              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  UNIT 3: Developer Portal (Website)                                 │
│  ─────────────────────────────────                                  │
│  • Deployed to: Vercel (same Next.js app as Unit 2)                 │
│  • Framework: Next.js 14+ (App Router)                              │
│  • Purpose: Sign up, get license key, manage plan, pay via Razorpay │
│  • Pages: Landing, Login, Dashboard, Pricing, Docs                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Communication between units:**

```
SDK (Python, local)  ──── HTTPS (once/day) ────►  License Server (Vercel)
                         Payload: {key, count}         │
                         Response: {valid, limit}       │
                                                       ▼
                                                  Supabase (Postgres)
                                                       ▲
Developer Portal (Browser)  ─── Supabase Auth ────────┘
                                Razorpay Webhook ──────┘
```

---

## 2. Tech Stack

### Python SDK

| Layer | Technology | Version | Why |
|---|---|---|---|
| **Language** | Python | 3.9+ | Widest adoption in AI/ML ecosystem |
| **Build System** | Hatchling | latest | Modern, fast Python build backend |
| **Package Manager** | pip / PyPI | — | Standard Python distribution |
| **Data Validation** | Pydantic | v2.0+ | Type-safe models, YAML schema validation |
| **YAML Parsing** | PyYAML | 6.0+ | Read policy files |
| **HTTP Client** | httpx | 0.25+ | Async-capable, modern HTTP (for license sync) |
| **Token Counting** | tiktoken | 0.5+ | OpenAI's official BPE tokenizer |
| **PII Detection** | regex (stdlib) | — | Zero-dependency PII patterns |
| **PII Detection (optional)** | presidio-analyzer | 2.2+ | Microsoft's NER-based PII (optional install) |
| **LLM Client** | openai | 1.0+ | Wrap OpenAI API calls |
| **CLI Framework** | click | 8.0+ | Simple, battle-tested CLI builder |
| **Testing** | pytest | 7.0+ | Test runner |
| **Testing (async)** | pytest-asyncio | 0.21+ | Async test support |
| **Mocking** | pytest-mock | — | Mock OpenAI calls in tests |
| **Linter** | ruff | 0.1+ | Fast Python linter + formatter |
| **Type Checker** | mypy | 1.0+ | Static type analysis |

### License Server + Developer Portal

| Layer | Technology | Version | Why |
|---|---|---|---|
| **Framework** | Next.js | 14+ | Full-stack React, API routes, SSR |
| **Language** | TypeScript | 5.0+ | Type safety for server code |
| **Runtime** | Node.js | 18+ | Vercel runtime |
| **Database** | Supabase (Postgres) | — | Free tier, built-in auth, REST API |
| **Auth** | Supabase Auth | — | Email/password, magic links |
| **Payments** | Razorpay | — | Indian payment gateway, UPI support |
| **Hosting** | Vercel | — | Free hobby tier, serverless functions |
| **Styling** | Tailwind CSS | 3.0+ | Rapid UI development |
| **Crypto** | Node.js crypto | built-in | SHA-256 hashing for license keys |

### CI/CD

| Tool | Purpose |
|---|---|
| **GitHub Actions** | Run tests, lint, type-check on every push/PR |
| **TestPyPI** | Test package publishing before real PyPI |
| **Vercel Git Integration** | Auto-deploy portal on push to `main` |

---

## 3. Project Structure (Full Tree)

```
guardian-runtime/                    # ← GitHub repo root
│
├── guardian/                        # ← Python SDK package (this ships to PyPI)
│   ├── __init__.py                  #    Guardian class, __version__, from_policy()
│   │
│   ├── core/                        #    Core orchestration layer
│   │   ├── __init__.py
│   │   ├── engine.py                #    Main execution engine (wraps full flow)
│   │   ├── policy.py                #    YAML policy loader + Pydantic models
│   │   ├── analysis.py              #    GuardianAnalysisSheet builder
│   │   ├── license.py               #    License key validator + daily sync
│   │   ├── storage.py               #    ~/.guardian/ local file manager
│   │   └── config.py                #    SDK configuration constants
│   │
│   ├── guards/                      #    Input & Output validation
│   │   ├── __init__.py
│   │   ├── input_guard.py           #    Orchestrates all input checks
│   │   ├── output_guard.py          #    Orchestrates all output checks
│   │   └── validators/              #    Individual check implementations
│   │       ├── __init__.py
│   │       ├── pii.py               #    PII regex detection
│   │       ├── jailbreak.py         #    Jailbreak pattern matching
│   │       ├── hallucination.py     #    LLM-as-judge hallucination check
│   │       ├── profanity.py         #    Profanity keyword filter
│   │       ├── scope.py             #    Topic boundary enforcement
│   │       └── custom.py            #    User-defined custom validators
│   │
│   ├── finops/                      #    Token economics & cost control
│   │   ├── __init__.py
│   │   ├── token_counter.py         #    tiktoken wrapper for counting
│   │   ├── cost_calculator.py       #    Model-specific $/token tables
│   │   ├── budget_manager.py        #    Per-agent, per-session budget tracking
│   │   ├── loop_detector.py         #    Detect recursive agent loops
│   │   └── router.py                #    Auto model downgrade/routing
│   │
│   ├── tools/                       #    Agent tool governance
│   │   ├── __init__.py
│   │   ├── tool_governor.py         #    Allowlist, denylist, rate limits
│   │   └── arg_validator.py         #    Tool argument regex/schema validation
│   │
│   ├── logging/                     #    Local-only logging
│   │   ├── __init__.py
│   │   ├── logger.py                #    Main logger (dispatches to sinks)
│   │   └── sinks/
│   │       ├── __init__.py
│   │       ├── jsonl.py             #    Write to ~/.guardian/logs/*.jsonl
│   │       └── console.py           #    Pretty-print to terminal
│   │
│   ├── integrations/                #    Framework connectors
│   │   ├── __init__.py
│   │   ├── openai_wrapper.py        #    Wrap openai.chat.completions.create()
│   │   └── langchain.py             #    LangChain BaseCallbackHandler
│   │
│   └── cli/                         #    Command-line interface
│       ├── __init__.py
│       ├── main.py                  #    CLI entry point (click group)
│       ├── init.py                  #    `guardian init --key KEY`
│       ├── validate.py              #    `guardian validate policy.yaml`
│       ├── status.py                #    `guardian status` (show plan, usage)
│       └── logs.py                  #    `guardian logs` (view local logs)
│
├── tests/                           #    All tests
│   ├── unit/
│   │   ├── test_pii.py
│   │   ├── test_jailbreak.py
│   │   ├── test_hallucination.py
│   │   ├── test_token_counter.py
│   │   ├── test_cost_calculator.py
│   │   ├── test_policy.py
│   │   ├── test_input_guard.py
│   │   ├── test_output_guard.py
│   │   ├── test_budget_manager.py
│   │   ├── test_tool_governor.py
│   │   ├── test_storage.py
│   │   └── test_license.py
│   ├── integration/
│   │   ├── test_full_flow.py        #    Policy → Guard → LLM → Log
│   │   └── test_langchain.py
│   └── conftest.py                  #    Shared fixtures (mock OpenAI, etc.)
│
├── examples/                        #    Copy-paste starter scripts
│   ├── quickstart.py
│   ├── langchain_rag.py
│   ├── cost_tracking.py
│   └── tool_governance.py
│
├── policies/                        #    Example YAML policies
│   ├── minimal.yaml
│   ├── production.yaml
│   └── enterprise.yaml
│
├── portal/                          #    Next.js developer portal + license API
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 #    Landing page
│   │   ├── login/page.tsx           #    Supabase Auth login
│   │   ├── signup/page.tsx          #    Signup + auto-generate free key
│   │   ├── dashboard/page.tsx       #    Show license key, usage count, plan
│   │   ├── pricing/page.tsx         #    Plans + Razorpay checkout
│   │   └── api/
│   │       ├── validate/route.ts    #    POST /api/validate (SDK daily sync)
│   │       ├── keys/route.ts        #    POST /api/keys (generate new key)
│   │       └── billing/
│   │           ├── checkout/route.ts    #    Create Razorpay order
│   │           └── webhook/route.ts     #    Razorpay payment confirmation
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── PricingCard.tsx
│   │   ├── UsageMeter.tsx
│   │   └── LicenseKeyDisplay.tsx
│   ├── lib/
│   │   ├── supabase-server.ts       #    Supabase server client
│   │   ├── supabase-browser.ts      #    Supabase browser client
│   │   └── razorpay.ts              #    Razorpay SDK setup
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── .github/
│   └── workflows/
│       └── ci.yml                   #    Test + lint on push
│
├── pyproject.toml                   #    Python package config (hatchling)
├── README.md                        #    Public-facing docs
├── PLAN.md                          #    Execution timeline
├── ARCHITECTURE.md                  #    This file
├── CHANGELOG.md                     #    Release history
├── LICENSE                          #    Apache-2.0
└── .gitignore
```

---

## 4. Component Breakdown

### 4.1 CLI Layer

**Location:** `guardian/cli/`  
**Framework:** `click` (Python)  
**Entry Point:** `guardian/cli/main.py`  
**Registered in:** `pyproject.toml` → `[project.scripts]` → `guardian = "guardian.cli.main:cli"`

```
guardian (CLI root group)
│
├── guardian init --key <LICENSE_KEY>
│   Purpose: Store license key locally
│   File: cli/init.py
│   Function: init_command(key: str)
│   Calls: core/storage.py → LocalStorage.save_license(key)
│   Creates: ~/.guardian/config.json
│   Output: "✅ Guardian initialized. Plan: free. Run `guardian status` to verify."
│
├── guardian validate <POLICY_FILE>
│   Purpose: Check YAML policy file for errors
│   File: cli/validate.py
│   Function: validate_command(policy_file: str)
│   Calls: core/policy.py → load_policy(path)
│   Output: "✅ Policy valid. 2 agents configured." or detailed error messages
│
├── guardian status
│   Purpose: Show current license, plan, and usage
│   File: cli/status.py
│   Function: status_command()
│   Reads: ~/.guardian/config.json, ~/.guardian/usage.json
│   Output:
│     License: gdn_live_****...****abcd
│     Plan: starter
│     Checks this month: 342 / 10,000
│     Last sync: 2026-06-15 09:30:00
│     Status: ACTIVE ✅
│
└── guardian logs [--tail N] [--severity high]
    Purpose: View local violation logs
    File: cli/logs.py
    Function: logs_command(tail: int, severity: str)
    Reads: ~/.guardian/logs/*.jsonl
    Output: Pretty-printed violation log entries
```

**Implementation detail — `main.py`:**

```python
# guardian/cli/main.py
import click

@click.group()
@click.version_option()
def cli():
    """⛨ Guardian Runtime — Local-first AI governance."""
    pass

# Import and register subcommands
from guardian.cli.init import init_command
from guardian.cli.validate import validate_command
from guardian.cli.status import status_command
from guardian.cli.logs import logs_command

cli.add_command(init_command, "init")
cli.add_command(validate_command, "validate")
cli.add_command(status_command, "status")
cli.add_command(logs_command, "logs")
```

---

### 4.2 Core Engine

**Location:** `guardian/core/engine.py`  
**Purpose:** Orchestrates the full check pipeline (input → LLM → output → log)

```
engine.py
│
├── class GuardianEngine
│   ├── __init__(self, policy: Policy, storage: LocalStorage, license: LicenseManager)
│   │   Initializes all sub-components from the loaded policy
│   │
│   ├── complete(self, model, messages, agent_id, session_id, **kwargs) → GuardianResponse
│   │   The main method. Full pipeline:
│   │   │
│   │   ├── Step 1: license.check_or_sync()
│   │   │   Verifies license is valid. If >24hrs since last sync, pings server.
│   │   │
│   │   ├── Step 2: storage.check_usage_limit()
│   │   │   Reads ~/.guardian/usage.json. If checks >= plan limit, block.
│   │   │
│   │   ├── Step 3: input_guard.check(user_message, agent_id)
│   │   │   Runs PII scan → secret scan → jailbreak scan → scope check
│   │   │   If blocked → return GuardianResponse(blocked=True)
│   │   │
│   │   ├── Step 4: budget_manager.pre_check(agent_id, estimated_cost)
│   │   │   If over budget → optionally downgrade model via router
│   │   │
│   │   ├── Step 5: openai_client.chat.completions.create(...)
│   │   │   Actual LLM call to OpenAI (using DEVELOPER's API key)
│   │   │
│   │   ├── Step 6: output_guard.check(prompt, response, agent_id)
│   │   │   Runs PII scan → hallucination judge → profanity filter
│   │   │
│   │   ├── Step 7: budget_manager.record(agent_id, actual_cost)
│   │   │   Updates local cost tracking
│   │   │
│   │   ├── Step 8: storage.increment_usage()
│   │   │   Bumps check count in ~/.guardian/usage.json
│   │   │
│   │   ├── Step 9: logger.log(analysis_sheet)
│   │   │   Writes to local JSONL file
│   │   │
│   │   └── Return: GuardianResponse(content, blocked, analysis)
│   │
│   └── get_cost_report(self, agent_id) → dict
│       Returns spend breakdown from local budget tracking
```

---

### 4.3 Input Guard

**Location:** `guardian/guards/input_guard.py`  
**Purpose:** Pipeline that checks user input before sending to LLM

```
input_guard.py
│
├── class InputGuard
│   ├── __init__(self, pii_detector, jailbreak_detector, scope_checker, custom_validators)
│   │
│   ├── @classmethod from_policy(cls, policy, agent_id) → InputGuard
│   │   Reads agent config from policy and instantiates relevant validators
│   │
│   └── check(self, text: str, agent_id: str) → InputCheckResult
│       Pipeline:
│       │
│       ├── 1. pii_detector.detect(text)
│       │   Returns: list[PIIMatch]
│       │   If any found + policy says block → blocked=True
│       │
│       ├── 2. jailbreak_detector.detect(text)
│       │   Returns: JailbreakResult
│       │   If is_jailbreak=True → blocked=True
│       │
│       ├── 3. scope_checker.check(text) (if configured)
│       │   Returns: ScopeResult
│       │   If off_topic=True → blocked=True
│       │
│       └── 4. custom_validators (if any registered)
│           Returns: list[ValidationResult]
│
└── @dataclass InputCheckResult
    ├── blocked: bool
    ├── reason: str | None
    ├── block_message: str | None
    ├── pii_matches: list[PIIMatch]
    ├── jailbreak_detected: bool
    ├── violations: list[Violation]
    └── timestamp: datetime
```

#### 4.3.1 PII Detector

**Location:** `guardian/guards/validators/pii.py`  
**Dependencies:** `re` (stdlib only — zero external deps)

```
pii.py
│
├── enum PIIType
│   SSN, CREDIT_CARD, EMAIL, PHONE, AADHAAR, PAN, UPI_ID, PASSPORT, SECRET
│
├── @dataclass PIIMatch
│   ├── pii_type: PIIType
│   ├── matched_text: str          # the actual matched string
│   ├── start: int                 # char index start
│   ├── end: int                   # char index end
│   └── confidence: float          # 0.0 - 1.0
│
├── dict PII_PATTERNS (PIIType → compiled regex)
│   │
│   ├── SSN:         \b\d{3}-\d{2}-\d{4}\b
│   │                Example: "123-45-6789"
│   │
│   ├── CREDIT_CARD: \b(?:\d{4}[-\s]?){3}\d{4}\b
│   │                Example: "4111 1111 1111 1111"
│   │                Note: Add Luhn checksum validation as post-filter
│   │
│   ├── AADHAAR:     \b[2-9]\d{3}\s?\d{4}\s?\d{4}\b
│   │                Example: "2345 6789 0123"
│   │                Note: Aadhaar never starts with 0 or 1
│   │
│   ├── PAN:         \b[A-Z]{5}\d{4}[A-Z]\b
│   │                Example: "ABCDE1234F"
│   │                Note: 4th char indicates holder type (P=Person, C=Company)
│   │
│   ├── UPI_ID:      Regex + allowlist gate (suffix checked FIRST, before flagging)
│   │
│   │   Detection order (critical — must follow this exactly):
│   │   Step 1. Candidate regex: \b[\w.\-]+@([a-z]{2,})\b
│   │           Captures the domain part in group(1)
│   │   Step 2. BEFORE flagging: check if group(1) is in KNOWN_UPI_SUFFIXES
│   │           If suffix NOT in set → discard immediately (it's an email)
│   │           If suffix IS in set → flag as UPI_ID
│   │
│   │   This means user@gmail.com is NEVER flagged. The suffix gate runs
│   │   inside detect() before any PIIMatch object is created.
│   │
│   │   Implementation:
│   │     for match in UPI_CANDIDATE_PATTERN.finditer(text):
│   │         suffix = match.group(1).lower()        # e.g. "gmail", "ybl"
│   │         if suffix not in KNOWN_UPI_SUFFIXES:   # <- gate, not post-filter
│   │             continue                           # discard — it's an email
│   │         matches.append(PIIMatch(pii_type=PIIType.UPI_ID, ...))
│   │
│   │   Examples that PASS gate: user@ybl, name@paytm, handle@oksbi
│   │   Examples that FAIL gate (correctly ignored): user@gmail.com,
│   │           user@outlook.com, admin@company.co.in
│   │
│   ├── EMAIL:       \b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b
│   │                Example: "user@example.com"
│   │                Note: EMAIL pattern requires a dot in domain (e.g. .com).
│   │                This is the structural difference from UPI IDs, which
│   │                never contain a dot in the suffix part.
│   │
│   ├── PHONE:       (Indian) (?:\+91[-\s]?)?\d{10}
│   │                (US)     (?:\+1[-\s]?)?(?:\(\d{3}\)|\d{3})[-\s]?\d{3}[-\s]?\d{4}
│   │
│   └── PASSPORT:    \b[A-Z]\d{7}\b
│                    Example: "J1234567"
│
├── class PIIDetector
│   ├── __init__(self, enabled_types: list[PIIType] | None)
│   │
│   ├── detect(self, text: str) → list[PIIMatch]
│   │   For most types: iterate PII_PATTERNS[type].finditer(text)
│   │   For UPI_ID specifically:
│   │       iterate UPI_CANDIDATE_PATTERN.finditer(text)
│   │       → suffix gate (KNOWN_UPI_SUFFIXES check) happens here
│   │       → only matching suffixes become PIIMatch objects
│   │   For SECRET specifically:
│   │       iterate CREDENTIAL_PATTERNS_HIGH first (confidence 0.95)
│   │       → then CREDENTIAL_PATTERNS_MEDIUM (confidence 0.70)
│   │       → MEDIUM matches overlapping HIGH matches are discarded
│   │
│   ├── _detect_secrets(self, text: str) → list[PIIMatch]
│   │   Two-tier secret detection:
│   │   Tier 1: HIGH confidence — exact prefix match (sk-, AKIA, ghp_, etc.)
│   │   Tier 2: MEDIUM confidence — generic KEY=value patterns
│   │   Overlap dedup: if a MEDIUM match overlaps a HIGH match, discard MEDIUM
│   │
│   ├── has_pii(self, text: str) → bool
│   └── redact(self, text: str) → str
│       Replaces matches with [AADHAAR_REDACTED], [PAN_REDACTED], [SECRET_REDACTED], etc.
│
├── UPI_CANDIDATE_PATTERN: re.Pattern
│   re.compile(r"\b[\w.\-]+@([a-z]{2,})\b", re.IGNORECASE)
│   Note: this pattern is intentionally NOT stored in PII_PATTERNS dict.
│   It is used only internally by detect() for UPI gating.
│
└── KNOWN_UPI_SUFFIXES: set[str]
    {
      "ybl",      # Yes Bank (PhonePe)
      "paytm",    # Paytm
      "oksbi",    # State Bank of India
      "okaxis",   # Axis Bank
      "okicici",  # ICICI Bank
      "okhdfcbank", # HDFC Bank
      "upi",      # Generic UPI
      "apl",      # Amazon Pay
      "ibl",      # IndusInd Bank
      "axl",      # Airtel Payments
      "fbl",      # Federal Bank
      "pingpay",  # Google Pay
      "gpay",     # Google Pay alternate
    }
    ⚠️  Suffix check runs BEFORE a PIIMatch is created — not as a post-filter.
    Adding new suffixes here is all that's needed to support new UPI handles.

├── CREDENTIAL_PATTERNS_HIGH: list[tuple[str, re.Pattern, float]]
│   HIGH confidence (0.95) — exact prefix match, block immediately:
│   │
│   ├── openai_api_key:     \bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b
│   │                       Example: "sk-proj-abc123def456..."
│   │
│   ├── anthropic_api_key:  \bsk-ant-[A-Za-z0-9_-]{20,}\b
│   │                       Example: "sk-ant-api03-xyz..."
│   │
│   ├── aws_access_key:     \bAKIA[0-9A-Z]{16}\b
│   │                       Example: "AKIAIOSFODNN7EXAMPLE"
│   │
│   ├── github_token:       \bgh[pousr]_[A-Za-z0-9_]{36,}\b
│   │                       Example: "ghp_xxxxxxxxxxxx..."
│   │
│   ├── stripe_key:         \b[sp]k_(?:live|test)_[A-Za-z0-9]{20,}\b
│   │                       Example: "sk_live_51J4abc..."
│   │
│   ├── razorpay_key:       \brzp_(?:live|test)_[A-Za-z0-9]{14,}\b
│   │                       Example: "rzp_live_abcdef123456"
│   │
│   ├── groq_api_key:       \bgsk_[A-Za-z0-9]{20,}\b
│   │                       Example: "gsk_abc123def456..."
│   │
│   ├── gcp_api_key:        \bAIza[0-9A-Za-z_-]{35}\b
│   │                       Example: "AIzaSyA1B2C3D4E5..."
│   │
│   ├── slack_token:        \bxox[bpoas]-[A-Za-z0-9-]{10,}\b
│   │                       Example: "xoxb-123-456-abc"
│   │
│   ├── huggingface_token:  \bhf_[A-Za-z0-9]{20,}\b
│   │                       Example: "hf_abcdef123456..."
│   │
│   └── private_key_block:  -----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----
│
├── CREDENTIAL_PATTERNS_MEDIUM: list[tuple[str, re.Pattern, float]]
│   MEDIUM confidence (0.70) — generic KEY=value patterns:
│   │
│   ├── generic_env_secret: API_KEY|SECRET_KEY|ACCESS_TOKEN|... = "value"
│   │                       Catches env-style assignments
│   │
│   └── bearer_token:       Bearer [A-Za-z0-9_.-]{20,}
│                           Catches authorization headers
│
│   ⚠️  Like UPI, secrets are NOT in PII_PATTERNS — handled in _detect_secrets().
│   HIGH matches are checked first. MEDIUM matches that overlap HIGH are discarded.
```

#### 4.3.2 Jailbreak Detector

**Location:** `guardian/guards/validators/jailbreak.py`  
**Dependencies:** `re` (stdlib only)

```
jailbreak.py
│
├── @dataclass JailbreakResult
│   ├── is_jailbreak: bool
│   ├── confidence: float
│   ├── pattern_matched: str | None
│   └── category: str | None
│       Categories: "dan", "instruction_override", "role_play",
│                   "encoding", "extraction"
│
├── list JAILBREAK_PATTERNS: list[tuple[str, str]]
│   50+ patterns organized by category:
│   │
│   ├── DAN variants (8 patterns)
│   │   "do anything now", "DAN mode", "developer mode enabled"
│   │
│   ├── Instruction Override (10 patterns)
│   │   "ignore all previous instructions", "forget everything",
│   │   "new instructions:", "override system prompt"
│   │
│   ├── Role Play Injection (8 patterns)
│   │   "pretend you are an unrestricted", "act as uncensored",
│   │   "you are now free from all guidelines"
│   │
│   ├── Encoding Tricks (5 patterns)
│   │   base64 encoded strings, "decode this base64/hex/rot13"
│   │
│   └── System Prompt Extraction (6 patterns)
│       "reveal your system prompt", "what are your instructions"
│
├── class JailbreakDetector
│   ├── __init__(self)
│   │   Compiles all regex patterns at init (once)
│   │
│   └── detect(self, text: str) → JailbreakResult
│       Iterates compiled patterns, returns first match
│       If no match: JailbreakResult(is_jailbreak=False)
│
└── Future: semantic similarity matching using embeddings
    (v0.2 — compare input embedding against known jailbreak corpus)
```

#### 4.3.3 Scope Checker

**Location:** `guardian/guards/validators/scope.py`  
**Dependencies:** `re` (keyword matching), optionally `openai` (semantic matching)

```
scope.py
│
├── @dataclass ScopeResult
│   ├── in_scope: bool
│   ├── matched_topic: str | None
│   └── confidence: float
│
├── class ScopeChecker
│   ├── __init__(self, allowed_topics: list[str], block_message: str)
│   │
│   ├── check_keyword(self, text: str) → ScopeResult
│   │   Simple keyword matching against allowed_topics list
│   │   Fast, no LLM call needed. Good enough for v0.1.
│   │
│   └── check_semantic(self, text: str) → ScopeResult  (v0.2)
│       Uses OpenAI embeddings to check semantic similarity
│       between the query and allowed topics
│       Threshold: cosine_similarity > 0.7 → in scope
```

---

### 4.4 Output Guard

**Location:** `guardian/guards/output_guard.py`  
**Purpose:** Pipeline that checks LLM response before returning to user

```
output_guard.py
│
├── class OutputGuard
│   ├── __init__(self, pii_detector, hallucination_detector, profanity_filter, ...)
│   │
│   ├── @classmethod from_policy(cls, policy, agent_id) → OutputGuard
│   │
│   └── check(self, prompt, response, context, agent_id) → OutputCheckResult
│       Pipeline:
│       │
│       ├── 1. pii_detector.detect(response)
│       │   Reuses same PIIDetector from input_guard
│       │
│       ├── 2. hallucination_detector.check(prompt, response, context)
│       │   LLM-as-judge call (costs extra tokens)
│       │   Only runs if hallucination_check: true in policy
│       │
│       ├── 3. profanity_filter.check(response)
│       │   Keyword-based. No LLM call needed.
│       │
│       └── 4. competitor_blocker.check(response)  (if configured)
│           Simple substring match against competitor names
│
└── @dataclass OutputCheckResult
    ├── violations: list[Violation]
    ├── pii_matches: list[PIIMatch]
    ├── hallucination_verdict: str  # "grounded" | "partially_grounded" | "hallucinated"
    └── timestamp: datetime
```

#### 4.4.1 Hallucination Detector

**Location:** `guardian/guards/validators/hallucination.py`  
**Dependencies:** `litellm` (provides a universal API to call OpenAI, Anthropic, Gemini, Ollama, etc. using developer's keys)

```
hallucination.py
│
├── JUDGE_SYSTEM_PROMPT: str
│   "You are a hallucination detector..."
│
├── JUDGE_USER_PROMPT_TEMPLATE: str
│   Template with {context}, {question}, {response} placeholders
│
├── @dataclass HallucinationResult
│   ├── verdict: str             # "grounded" | "partially_grounded" | "hallucinated"
│   ├── confidence: float
│   ├── unsupported_claims: list[str]
│   ├── explanation: str
│   └── is_hallucination: bool   # convenience: verdict == "hallucinated"
│
├── class HallucinationDetector
│   ├── __init__(self, provider: str, judge_model: str, threshold: float)
│   │   provider: "openai" | "anthropic" | "ollama" | "gemini"
│   │   judge_model: defaults to "gpt-4o-mini" (or "llama3" for ollama)
│   │   threshold: confidence above which to flag (default 0.7)
│   │
│   └── check(self, question, response, context) → HallucinationResult
│       Makes API call using LiteLLM with:
│       │   model = f"{self.provider}/{self.judge_model}"
│       │   response_format = {"type": "json_object"}
│       │   temperature = 0.0 (deterministic)
│       │
│       Parses JSON response into HallucinationResult
│
│   ⚠️  IMPORTANT: This uses the developer's existing API keys or local 
│      Ollama instance. Cost is highly variable ($0.00 for local, ~$0.0002 
│      for gpt-4o-mini).
│
└── By leveraging LiteLLM, Guardian is 100% model-agnostic for judging.
```

#### 4.4.2 Profanity Filter

**Location:** `guardian/guards/validators/profanity.py`  
**Dependencies:** None (pure Python keyword list)

```
profanity.py
│
├── PROFANITY_WORDS: set[str]
│   ~400 words organized by severity (low, medium, high)
│   Source: public profanity word lists
│
├── @dataclass ProfanityResult
│   ├── has_profanity: bool
│   ├── matched_words: list[str]
│   └── severity: str
│
└── class ProfanityFilter
    ├── __init__(self, custom_words: list[str] | None)
    └── check(self, text: str) → ProfanityResult
```

---

### 4.5 FinOps Engine

**Location:** `guardian/finops/`  
**Purpose:** Track, limit, and optimize LLM spending locally

```
finops/
│
├── token_counter.py
│   ├── Uses: tiktoken library
│   │
│   ├── count_tokens(text: str, model: str) → int
│   │   Gets the right BPE encoding for the model
│   │   Uses @lru_cache for encoding objects
│   │
│   └── count_messages_tokens(messages: list[dict], model: str) → int
│       Accounts for ChatML overhead (role tokens, separators)
│       Formula: sum(msg tokens) + 3 per message + 3 for reply priming
│
├── cost_calculator.py
│   ├── MODEL_COST_PER_1K: dict[str, dict[str, float]]
│   │   {
│   │     "gpt-4o":        {"input": 0.005,   "output": 0.015},
│   │     "gpt-4o-mini":   {"input": 0.00015, "output": 0.0006},
│   │     "gpt-3.5-turbo": {"input": 0.0005,  "output": 0.0015},
│   │     "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
│   │     # ... all major models
│   │   }
│   │
│   ├── estimate_cost(input_tokens, output_tokens, model) → float
│   │   Returns cost in USD
│   │
│   └── get_supported_models() → list[str]
│
├── budget_manager.py
│   ├── class BudgetManager
│   │   Tracks per-agent, per-session spend in memory (not persisted)
│   │   │
│   │   ├── __init__(self, policy: Policy)
│   │   ├── pre_check(self, agent_id, estimated_cost) → BudgetDecision
│   │   │   Returns: ALLOW | DOWNGRADE | BLOCK
│   │   │   If spend + estimated > daily_budget → BLOCK
│   │   │   If spend + estimated > threshold (80%) → DOWNGRADE
│   │   │
│   │   ├── record(self, agent_id, session_id, actual_cost)
│   │   │   Adds to running totals
│   │   │
│   │   └── get_report(self, agent_id) → dict
│   │       Returns: {today: $X, budget: $Y, utilization: Z%}
│   │
│   └── @dataclass BudgetDecision
│       ├── action: str          # "allow" | "downgrade" | "block"
│       ├── suggested_model: str | None
│       └── reason: str
│
├── loop_detector.py
│   ├── class LoopDetector
│   │   Detects when an agent sends the same/similar prompt repeatedly
│   │   │
│   │   ├── __init__(self, max_retries: int, similarity_threshold: float)
│   │   │   max_retries: default 3
│   │   │   similarity_threshold: default 0.90
│   │   │
│   │   ├── check(self, prompt: str, session_id: str) → bool
│   │   │   Stores last N prompts per session (in memory)
│   │   │   Compares using SequenceMatcher (stdlib difflib)
│   │   │   If similarity > threshold for N consecutive prompts → True
│   │   │
│   │   └── reset(self, session_id: str)
│   │
│   └── Uses: difflib.SequenceMatcher (stdlib — no external deps)
│
└── router.py
    ├── class ModelRouter
    │   ├── __init__(self, routing_rules: list[RoutingRule])
    │   │
    │   └── select_model(self, default_model, agent_id, token_count, budget_state) → str
    │       Evaluates rules in order:
    │       - if budget > 80% → downgrade to cheap model
    │       - if token_count > 2000 → use stronger model
    │       - else → use default
    │
    └── @dataclass RoutingRule
        ├── condition: str       # parsed from YAML
        ├── model: str
        └── reason: str
```

---

### 4.6 Tool Governor

**Location:** `guardian/tools/`  
**Purpose:** Control which tools AI agents can invoke

```
tools/
│
├── tool_governor.py
│   ├── class ToolGovernor
│   │   ├── __init__(self, allowed, denied, rate_limits, arg_validators)
│   │   │
│   │   ├── @classmethod from_policy(cls, policy, agent_id) → ToolGovernor
│   │   │
│   │   └── check_tool_call(self, tool_name, arguments, session_id) → ToolDecision
│   │       Pipeline:
│   │       │
│   │       ├── 1. Is tool_name in denied list? → BLOCK
│   │       ├── 2. Is tool_name in allowed list? (if allowlist configured)
│   │       │      Not in list → BLOCK
│   │       ├── 3. Rate limit check:
│   │       │      Count calls for this tool in this session
│   │       │      If count >= max_calls → BLOCK (rate limited)
│   │       └── 4. Argument validation:
│   │              Run regex patterns against argument values
│   │              If any fail → BLOCK (arg validation failed)
│   │
│   ├── @dataclass ToolDecision
│   │   ├── allowed: bool
│   │   ├── reason: str
│   │   └── tool_name: str
│   │
│   └── Internal state:
│       _call_counts: dict[str, dict[str, int]]
│       # { session_id: { tool_name: count } }
│       # Stored in memory only, resets per process
│
└── arg_validator.py
    ├── class ArgValidator
    │   └── validate(self, tool_name, arguments, rules) → list[str]
    │       Returns list of error messages (empty = all valid)
    │       Checks:
    │       ├── type validation (string, int, enum)
    │       ├── regex pattern matching
    │       └── enum value validation
    │
    └── Uses: re (stdlib)
```

---

### 4.7 Policy Engine

**Location:** `guardian/core/policy.py`  
**Dependencies:** `pyyaml`, `pydantic`

```
policy.py
│
├── function load_policy(path: str | Path) → Policy
│   Reads YAML file → validates with Pydantic → returns Policy object
│   Raises: PolicyValidationError with line numbers and details
│
├── class Policy (Pydantic BaseModel)
│   ├── version: str
│   ├── name: str
│   ├── environment: str | None        # "dev" | "staging" | "production"
│   ├── agents: dict[str, AgentPolicy]
│   ├── logging: LoggingConfig | None
│   ├── alerts: AlertConfig | None
│   └── compliance: ComplianceConfig | None
│   │
│   └── get_agent(self, agent_id: str) → AgentPolicy | None
│       Falls back to "default" agent if specific one not found
│
├── class AgentPolicy (Pydantic BaseModel)
│   ├── input_guard: InputGuardConfig | None
│   │   ├── pii_detection: bool
│   │   ├── pii_entities: list[str]
│   │   ├── jailbreak_detection: bool
│   │   └── scope: ScopeConfig | None
│   │       ├── allowed_topics: list[str]
│   │       └── block_message: str
│   │
│   ├── output_guard: OutputGuardConfig | None
│   │   ├── hallucination_check: bool
│   │   ├── pii_detection: bool
│   │   ├── profanity_filter: bool
│   │   └── competitor_block: list[str]
│   │
│   ├── cost: CostConfig | None
│   │   ├── daily_budget: float
│   │   ├── monthly_budget: float | None
│   │   ├── per_session_limit: float
│   │   ├── currency: str                # "USD"
│   │   ├── auto_downgrade: AutoDowngradeConfig | None
│   │   │   ├── enabled: bool
│   │   │   ├── threshold: float         # 0.0 - 1.0
│   │   │   └── target_model: str
│   │   └── loop_detection: LoopConfig | None
│   │       ├── max_retries: int
│   │       ├── similarity_threshold: float
│   │       └── action: str              # "block" | "block_and_alert"
│   │
│   └── tools: ToolConfig | None
│       ├── allowed: list[str]
│       ├── denied: list[str]
│       ├── rate_limits: dict[str, RateLimit]
│       │   └── RateLimit: { max_calls: int, per: str, cooldown_seconds: int }
│       └── argument_validation: dict[str, dict[str, ArgRule]]
│           └── ArgRule: { type: str, pattern: str, values: list[str] }
│
├── class LoggingConfig
│   ├── sink: str                   # "jsonl" | "console" | "both"
│   ├── log_level: str              # "ALL" | "VIOLATIONS_ONLY" | "HIGH_SEVERITY"
│   └── retention_days: int
│
└── class PolicyValidationError(Exception)
    Raised when YAML doesn't match schema
    Includes: field name, expected type, actual value, line number
```

---

### 4.8 Local Storage

**Location:** `guardian/core/storage.py`  
**Dependencies:** `json`, `os`, `pathlib` (all stdlib)

```
storage.py
│
├── Constants:
│   GUARDIAN_DIR  = Path.home() / ".guardian"
│   CONFIG_FILE   = GUARDIAN_DIR / "config.json"
│   USAGE_FILE    = GUARDIAN_DIR / "usage.json"
│   LOGS_DIR      = GUARDIAN_DIR / "logs"
│
├── class LocalStorage
│   │
│   ├── @staticmethod ensure_dirs()
│   │   Creates ~/.guardian/ and ~/.guardian/logs/ if they don't exist
│   │
│   ├── save_license(key: str, plan: str, limit: int, expiry: str)
│   │   Writes: ~/.guardian/config.json
│   │   Content:
│   │   {
│   │     "license_key": "gdn_live_abc123...",
│   │     "plan": "starter",
│   │     "check_limit": 10000,
│   │     "expiry": "2027-01-15",
│   │     "initialized_at": "2026-06-15T10:30:00Z"
│   │   }
│   │
│   ├── load_license() → dict | None
│   │   Reads config.json. Returns None if not initialized.
│   │
│   ├── increment_usage() → int
│   │   Reads ~/.guardian/usage.json
│   │   If month has changed → reset count to 0
│   │   Increment count by 1
│   │   Write back
│   │   Returns: new count
│   │
│   │   usage.json format:
│   │   {
│   │     "month": "2026-06",
│   │     "checks": 342,
│   │     "last_sync": "2026-06-15T09:30:00Z"
│   │   }
│   │
│   ├── get_usage() → dict
│   │   Returns current month's usage data
│   │
│   ├── check_usage_limit() → tuple[bool, int, int]
│   │   Returns: (within_limit, current_count, limit)
│   │   Reads from usage.json and config.json
│   │
│   ├── mark_synced(timestamp: str)
│   │   Updates last_sync in usage.json
│   │
│   └── get_log_path(date: str) → Path
│       Returns: ~/.guardian/logs/2026-06-15.jsonl
```

---

### 4.9 License Manager

**Location:** `guardian/core/license.py`  
**Dependencies:** `httpx` (HTTP client for daily sync)

```
license.py
│
├── LICENSE_SERVER_URL = "https://guardian-ai.dev/api/validate"
│
├── class LicenseManager
│   ├── __init__(self, storage: LocalStorage)
│   │
│   ├── check_or_sync(self) → LicenseStatus
│   │   Called at the START of every guardian.complete() call
│   │   │
│   │   ├── 1. Read config.json → get license_key
│   │   │      If no key → return UNINITIALIZED (SDK still works in free mode)
│   │   │
│   │   ├── 2. Read usage.json → get last_sync timestamp
│   │   │
│   │   ├── 3. If (now - last_sync) < 24 hours:
│   │   │      → Skip network call. Return VALID (trust local data).
│   │   │
│   │   └── 4. If (now - last_sync) >= 24 hours:
│   │          → Call sync_with_server()
│   │
│   ├── sync_with_server(self) → LicenseStatus
│   │   Makes HTTPS POST to LICENSE_SERVER_URL
│   │   │
│   │   Request body (THIS IS ALL WE EVER SEND):
│   │   {
│   │     "license_key": "gdn_live_abc123...",
│   │     "checks_used": 342
│   │   }
│   │   ⚠️  NO prompts. NO responses. NO API keys. NO violation details.
│   │
│   │   Response body:
│   │   {
│   │     "valid": true,
│   │     "plan": "starter",
│   │     "limit": 10000,
│   │     "expiry": "2027-01-15"
│   │   }
│   │   │
│   │   ├── If valid → update config.json with latest plan info
│   │   ├── If invalid → log warning, switch to free tier limits
│   │   └── If network error → fail open (allow SDK to keep working)
│   │       Guardian NEVER blocks your work due to our server being down
│   │
│   └── is_initialized(self) → bool
│       Returns True if config.json exists and has a key
│
├── @dataclass LicenseStatus
│   ├── status: str      # "valid" | "invalid" | "expired" | "uninitialized"
│   ├── plan: str
│   ├── limit: int
│   └── synced: bool      # was this a fresh sync or cached?
│
└── Design decisions:
    • Fail-open: if our server is down, SDK keeps working with cached data
    • Offline mode: Enterprise keys have expiry but no daily ping required
    • Grace period:
        - Days 1–7 after expiry: SDK continues to work (full functionality)
        - SDK prints a warning to terminal on every guardian.complete() call:
          "[GUARDIAN WARNING] Your license expired N day(s) ago.
           Grace period ends in (7-N) day(s). Renew at guardian-ai.dev"
        - Day 8+: SDK hard-blocks all calls. Returns GuardianExpiredError.
        - Portal reflects the same state via ExpiryWarningBanner (see §6)
        - Free plan: no expiry date — never enters grace period
    • No telemetry: we never send usage patterns, timings, or metadata
```

---

### 4.10 Logging System

**Location:** `guardian/logging/`  
**Purpose:** Write all checks and violations to local files (NEVER uploaded)

```
logging/
│
├── logger.py
│   ├── class GuardianLogger
│   │   ├── __init__(self, sinks: list[LogSink], log_level: str)
│   │   │
│   │   ├── @classmethod from_policy(cls, policy) → GuardianLogger
│   │   │   Reads policy.logging config
│   │   │   Creates appropriate sinks (jsonl, console, or both)
│   │   │
│   │   ├── log(self, analysis: AnalysisSheet)
│   │   │   Dispatches to all configured sinks
│   │   │
│   │   └── log_violation(self, violation: Violation, agent_id, session_id)
│   │       Logs a specific violation event
│   │
│   └── class LogSink (Protocol)
│       └── write(self, entry: dict) → None
│
├── sinks/jsonl.py
│   ├── class JSONLSink
│   │   ├── __init__(self, logs_dir: Path)
│   │   │   logs_dir defaults to ~/.guardian/logs/
│   │   │
│   │   └── write(self, entry: dict)
│   │       Appends one JSON line to ~/.guardian/logs/YYYY-MM-DD.jsonl
│   │       Each line is a complete, self-contained JSON object:
│   │       {
│   │         "timestamp": "2026-06-15T10:30:00Z",
│   │         "agent_id": "support-bot",
│   │         "session_id": "sess_abc123",
│   │         "type": "violation",
│   │         "violation_type": "pii_detected",
│   │         "severity": "high",
│   │         "detail": "Aadhaar number found in input",
│   │         "action": "blocked",
│   │         "model": "gpt-4",
│   │         "input_tokens": 312,
│   │         "output_tokens": 0,
│   │         "cost_usd": 0.0,
│   │         "policy_version": "1.0"
│   │       }
│   │
│   └── File rotation: one file per day, auto-created
│
└── sinks/console.py
    └── class ConsoleSink
        └── write(self, entry: dict)
            Pretty-prints violations to terminal with color codes
            Uses ANSI escape codes (no external dependency)
            [HIGH] 10:30:00 PII_DETECTED — Aadhaar number found in input → BLOCKED
```

---

### 4.11 Integrations

**Location:** `guardian/integrations/`

```
integrations/
│
├── openai_wrapper.py
│   Purpose: Wraps openai.chat.completions.create()
│   │
│   ├── class GuardianOpenAI
│   │   Extends or wraps the official OpenAI client
│   │   │
│   │   └── create(self, model, messages, **kwargs) → GuardianResponse
│   │       Internally calls self.engine.complete(...)
│   │       Returns response that includes .guardian_analysis
│   │
│   └── Developer's OpenAI API key is used directly
│       Guardian never stores, reads, or transmits the API key
│
└── langchain.py
    Purpose: LangChain callback handler
    │
    ├── class GuardianCallbackHandler(BaseCallbackHandler)
    │   ├── @classmethod from_policy(cls, path) → GuardianCallbackHandler
    │   │
    │   ├── on_llm_start(self, serialized, prompts, **kwargs)
    │   │   Runs input_guard.check() on each prompt
    │   │   If blocked → raises GuardianBlockedError
    │   │
    │   └── on_llm_end(self, response, **kwargs)
    │       Runs output_guard.check() on each generation
    │       If high severity violation → raises GuardianBlockedError
    │
    └── class GuardianBlockedError(Exception)
        Raised when Guardian blocks a request inside a LangChain chain
        Contains: violation details, severity, analysis sheet
```

---

## 5. License Key Server (Backend)

**Location:** `portal/app/api/`  
**Framework:** Next.js 14 API Routes (serverless functions on Vercel)  
**Database:** Supabase (Postgres)

```
API Routes:
│
├── POST /api/validate
│   Purpose: Daily sync endpoint. Called by Python SDK once per day.
│   │
│   Request:
│   {
│     "license_key": "gdn_live_abc123...",
│     "checks_used": 342
│   }
│   │
│   Logic:
│   1. Hash the incoming key: SHA-256(license_key)
│   2. Query Supabase: SELECT * FROM licenses WHERE key_hash = $1
│   3. If not found → return { "valid": false }
│   4. If found but expired → return { "valid": false, "reason": "expired" }
│   5. Update usage: UPDATE licenses SET checks_used = $1 WHERE id = $2
│   6. Return { "valid": true, "plan": "starter", "limit": 10000, "expiry": "2027-01-15" }
│   │
│   Response:
│   { "valid": true, "plan": "starter", "limit": 10000, "expiry": "..." }
│   │
│   Security:
│   - Rate limited: 10 requests per key per day (to prevent brute force)
│   - Key is always hashed before DB lookup (never stored raw)
│   - No auth header needed (the key itself IS the authentication)
│
├── POST /api/keys
│   Purpose: Generate a new license key for a user
│   Auth: Supabase JWT (user must be logged in)
│   │
│   Logic:
│   1. Verify Supabase auth token
│   2. Generate key: "gdn_live_" + crypto.randomBytes(16).toString("hex")
│   3. Hash key: SHA-256(key)
│   4. Insert into DB: { user_id, key_hash, plan: "free", limit: 500 }
│   5. Return raw key to user (shown ONCE, never retrievable again)
│   │
│   Response:
│   { "license_key": "gdn_live_a1b2c3d4e5f6...", "plan": "free", "limit": 500 }
│
├── POST /api/billing/checkout
│   Purpose: Create a Razorpay order for plan upgrade
│   Auth: Supabase JWT
│   │
│   Logic:
│   1. Read plan_id from request body
│   2. Create Razorpay order: razorpay.orders.create({ amount, currency: "INR" })
│   3. Return order_id to frontend (frontend opens Razorpay checkout modal)
│   │
│   Response:
│   { "order_id": "order_abc123", "amount": 80000, "currency": "INR" }
│
└── POST /api/billing/webhook
    Purpose: Razorpay payment confirmation webhook
    Auth: Razorpay webhook signature verification
    │
    Logic:
    1. Verify Razorpay signature (HMAC SHA-256)
    2. Extract payment details (user_id, plan_id)
    3. Update DB: UPDATE licenses SET plan = 'pro', limit = 100000 WHERE user_id = $1
    4. Return 200 OK
    │
    Security:
    - Webhook secret stored in env var RAZORPAY_WEBHOOK_SECRET
    - Signature verification prevents spoofed webhooks
```

---

## 6. Developer Portal (Frontend)

**Location:** `portal/app/`  
**Framework:** Next.js 14 (App Router)  
**Styling:** Tailwind CSS  
**Auth:** Supabase Auth (email + password)

```
Pages:
│
├── / (Landing Page)
│   Components: Hero, FeatureGrid, PricingPreview, Footer
│   Purpose: Explain Guardian, link to docs, CTA to sign up
│
├── /login
│   Components: LoginForm
│   Auth: supabase.auth.signInWithPassword()
│   Redirect: → /dashboard on success
│
├── /signup
│   Components: SignupForm
│   Auth: supabase.auth.signUp()
│   Post-signup: auto-call POST /api/keys to generate free license key
│   Redirect: → /dashboard (shows key for first time)
│
├── /dashboard
│   Components: LicenseKeyDisplay, UsageMeter, PlanBadge, ExpiryWarningBanner
│   Auth: Protected route (redirect to /login if not authenticated)
│   │
│   Shows:
│   ├── [BANNER] ExpiryWarningBanner   ← rendered at top, above all other content
│   │   Logic (computed from license.expiry):
│   │   │
│   │   ├── days_until_expiry = diff(expiry_date, today) in days
│   │   │
│   │   ├── If days_until_expiry > 7:   → No banner rendered
│   │   │
│   │   ├── If 0 < days_until_expiry <= 7:
│   │   │   → Yellow warning banner:
│   │   │   "⚠️  Your license expires in {N} day(s). Renew now to avoid interruption."
│   │   │   CTA button: "Renew Plan" → /pricing
│   │   │
│   │   ├── If days_until_expiry == 0:  (expires today)
│   │   │   → Orange urgent banner:
│   │   │   "🔔 Your license expires today. Renew now — you have a 7-day grace period."
│   │   │
│   │   └── If days_until_expiry < 0:   (already expired, within grace period)
│   │       days_in_grace = abs(days_until_expiry)
│   │       If days_in_grace <= 7:
│   │         → Red grace-period banner:
│   │         "🚨 Your license expired {N} day(s) ago. You are in the 7-day grace period.
│   │              Guardian is still working. Renew before grace period ends."
│   │         CTA button: "Renew Now" → /pricing
│   │       If days_in_grace > 7:
│   │         → Red hard-block banner:
│   │         "❌ Your license has expired and the grace period has ended.
│   │              Guardian SDK is now blocked. Renew to restore access."
│   │         CTA button: "Renew Now" → /pricing
│   │
│   │   Component props: { expiry: string | null, plan: string }
│   │   Note: Free plan has expiry=null (never expires, just has check limits)
│   │         Banner is only shown for paid plans (Starter, Pro, Enterprise)
│   │
│   ├── License key (masked: gdn_live_****...****abcd) with copy button
│   ├── Current plan (Free / Starter / Pro)
│   ├── Usage this month: 342 / 10,000 checks (progress bar)
│   ├── Key expiry date (with "In grace period" badge if applicable)
│   └── "Upgrade Plan" button → /pricing
│   │
│   Data source: Supabase query for logged-in user's license
│   Fields fetched: plan, check_limit, checks_used, expiry, active
│
├── /pricing
│   Components: PricingCard (x3), RazorpayCheckoutButton
│   │
│   Plans displayed:
│   ├── Free: ₹0 / 500 checks (current plan highlighted)
│   ├── Starter: ₹800/mo / 10,000 checks
│   └── Pro: ₹2,400/mo / 100,000 checks
│   │
│   Payment flow:
│   1. User clicks "Upgrade to Pro"
│   2. Frontend calls POST /api/billing/checkout
│   3. Opens Razorpay checkout modal (UPI, card, netbanking)
│   4. On success → Razorpay webhook → DB updated → page refreshes
│
└── /docs (optional, can link to external MkDocs site)
```

**Key Components:**

```
components/
│
├── LicenseKeyDisplay.tsx
│   Props: { keyValue: string, masked: boolean }
│   Shows masked key with "reveal" toggle and "copy" button
│   Uses: navigator.clipboard.writeText()
│
├── UsageMeter.tsx
│   Props: { current: number, limit: number }
│   Visual progress bar with percentage
│   Colors: green (0-60%), yellow (60-80%), red (80-100%)
│
├── PricingCard.tsx
│   Props: { name, price, features, isCurrent, onUpgrade }
│   Highlights current plan with badge
│   Disabled state for current/lower plans
│
└── Navbar.tsx
    Shows: Logo, Docs link, Dashboard link, Logout button
    Auth-aware: shows Login/Signup when logged out
```

---

## 7. Data Models

### Python SDK Data Models (Pydantic)

```python
# All defined in guardian/core/analysis.py

@dataclass
class Violation:
    type: str           # "pii", "jailbreak", "hallucination", "profanity",
                        # "competitor", "scope", "budget", "tool", "loop"
    severity: str       # "low", "medium", "high", "critical"
    detail: str         # Human-readable description
    action: str         # "blocked", "flagged", "allowed"
    metadata: dict      # Extra context (matched pattern, tool name, etc.)

@dataclass
class InputAnalysis:
    tokens: int
    estimated_cost: float
    pii_found: list[PIIMatch]
    jailbreak_detected: bool
    scope_check: str        # "in_scope" | "out_of_scope" | "not_configured"
    optimization_hint: str | None  # "prompt can be shortened by 40%"
    status: str             # "ALLOWED" | "BLOCKED"
    block_reason: str | None

@dataclass
class OutputAnalysis:
    tokens: int
    actual_cost: float
    hallucination_risk: str   # "grounded" | "partially_grounded" | "hallucinated"
    pii_found: list[PIIMatch]
    profanity_found: bool
    scope_status: str
    status: str               # "CLEAN" | "FLAGGED" | "BLOCKED"

@dataclass
class AnalysisSheet:
    input: InputAnalysis
    output: OutputAnalysis | None   # None if input was blocked
    session_budget: dict | None     # { spent, limit, remaining }
    timestamp: datetime
    agent_id: str
    session_id: str | None

@dataclass
class GuardianResponse:
    content: str               # The LLM response text (or block message)
    blocked: bool
    analysis: AnalysisSheet    # Full Guardian Analysis Sheet
    raw_response: object       # Original OpenAI response object (if not blocked)
```

---

## 8. Request Flow (End-to-End)

```
Developer calls: guardian.complete(model="gpt-4", messages=[...], agent_id="support-bot")
│
├── 1. LICENSE CHECK
│   license.py → check_or_sync()
│   ├── Read ~/.guardian/config.json
│   ├── If last_sync > 24h ago → POST to guardian-ai.dev/api/validate
│   │   Sends: { key, checks_used }
│   │   Gets: { valid, plan, limit }
│   └── If valid → continue. If invalid → warn but don't block (grace period).
│
├── 2. USAGE LIMIT CHECK
│   storage.py → check_usage_limit()
│   ├── Read ~/.guardian/usage.json → checks this month
│   ├── Read config.json → check_limit for plan
│   ├── If checks >= limit → BLOCK with upgrade prompt
│   └── If checks >= 80% of limit → WARN in analysis sheet
│
├── 3. INPUT GUARD
│   input_guard.py → check(user_message, agent_id="support-bot")
│   ├── pii.py → detect(text) → list[PIIMatch]
│   │   If Aadhaar found → Violation(type="pii", severity="high")
│   │   If API key found → Violation(type="pii", severity="critical", subtype="secret")
│   ├── jailbreak.py → detect(text) → JailbreakResult
│   │   If "ignore all instructions" → Violation(type="jailbreak", severity="critical")
│   └── scope.py → check(text) → ScopeResult (if configured)
│   │
│   If any blocking violation → RETURN GuardianResponse(blocked=True)
│
├── 4. COST PRE-CHECK
│   budget_manager.py → pre_check(agent_id, estimated_cost)
│   ├── token_counter.py → count_tokens(text, model) → 312 tokens
│   ├── cost_calculator.py → estimate_cost(312, model="gpt-4") → $0.002
│   ├── If spent + $0.002 > daily_budget → BLOCK
│   └── If spent + $0.002 > 80% of budget → DOWNGRADE model
│       router.py → select_model() → "gpt-3.5-turbo" (cheaper)
│
├── 5. LLM CALL (uses developer's API key, NOT ours)
│   openai.chat.completions.create(model=selected_model, messages=messages)
│   → response text + usage (input_tokens, output_tokens)
│
├── 6. OUTPUT GUARD
│   output_guard.py → check(prompt, response, agent_id="support-bot")
│   ├── pii.py → detect(response_text)
│   ├── hallucination.py → check(prompt, response, context)
│   │   Makes second LLM call (e.g. gpt-4o-mini or local llama3) for judging
│   │   Returns: "grounded" | "partially_grounded" | "hallucinated"
│   └── profanity.py → check(response_text)
│
├── 7. RECORD COST
│   budget_manager.py → record(agent_id, session_id, actual_cost)
│   cost_calculator.py → estimate_cost(input_tokens, output_tokens, model)
│
├── 8. INCREMENT USAGE
│   storage.py → increment_usage()
│   Writes to ~/.guardian/usage.json → checks: 343
│
├── 9. LOG LOCALLY
│   logger.py → log(analysis_sheet)
│   jsonl.py → write({...}) to ~/.guardian/logs/2026-06-15.jsonl
│   console.py → print("[CLEAN] gpt-4 | 312 in / 89 out | $0.002")
│
└── 10. RETURN
    GuardianResponse(
      content = "The capital of France is Paris.",
      blocked = False,
      analysis = AnalysisSheet(input=..., output=..., session_budget=...),
      raw_response = <OpenAI ChatCompletion object>
    )
```

---

## 9. YAML Policy Schema

Complete annotated schema with every possible field:

```yaml
# Full Guardian Policy Schema — all fields shown
# Only 'version' and 'agents' are required. Everything else is optional.

version: "1.0"                    # REQUIRED. Schema version.
name: "my-policy"                 # Policy name (for logs/display)
environment: production           # "dev" | "staging" | "production"

agents:
  # Each key is an agent_id. "default" is the fallback agent.
  default:
    input_guard:
      pii_detection: true             # Enable PII scanning
      pii_entities:                   # Which PII types to detect
        - ssn
        - credit_card
        - aadhaar                     # India DPDP Act
        - pan                         # India DPDP Act
        - upi_id                      # India DPDP Act
        - email
        - phone
        - passport
        - secret                      # API keys, tokens, credentials
      pii_action: block               # "block" | "redact" | "flag"
      jailbreak_detection: true       # Enable jailbreak scanning
      scope:
        allowed_topics:               # List of allowed topics
          - billing
          - account
          - product
        block_message: "I can only help with billing, account, and product."

    output_guard:
      hallucination_check: true       # Enable LLM-as-judge
      hallucination_provider: openai  # "openai", "anthropic", "ollama", "gemini"
      hallucination_model: gpt-4o-mini  # Model used for judging
      pii_detection: true             # Scan LLM responses for PII
      profanity_filter: true          # Block profane outputs
      competitor_block:               # Block mentions of competitors
        - "CompetitorA"
        - "CompetitorB"

    cost:
      daily_budget: 10.00            # Max $/day for this agent
      monthly_budget: 250.00         # Max $/month
      per_session_limit: 0.50        # Max $/session
      currency: USD
      auto_downgrade:
        enabled: true
        threshold: 0.80              # Trigger at 80% budget usage
        target_model: gpt-3.5-turbo  # Downgrade to this model
      loop_detection:
        max_retries: 3               # Block after 3 similar prompts
        similarity_threshold: 0.90
        action: block_and_alert      # "block" | "block_and_alert"

    tools:
      allowed:                       # Allowlist (if set, only these tools work)
        - search_kb
        - get_order_status
      denied:                        # Denylist (always blocked)
        - delete_user
        - execute_sql
      rate_limits:
        search_kb:
          max_calls: 20
          per: session
        create_ticket:
          max_calls: 3
          per: session
          cooldown_seconds: 30
      argument_validation:
        create_ticket:
          priority:
            type: enum
            values: [low, medium, high]
          customer_id:
            type: string
            pattern: "^CUST-[0-9]{6}$"

logging:
  sink: both                     # "jsonl" | "console" | "both"
  log_level: ALL                 # "ALL" | "VIOLATIONS_ONLY" | "HIGH_SEVERITY"
  retention_days: 90             # For local JSONL file cleanup
```

---

## 10. Local File System Layout

Everything Guardian stores on the developer's machine:

```
~/.guardian/                          # Created by `guardian init`
│
├── config.json                      # License key & plan info
│   {
│     "license_key": "gdn_live_a1b2c3d4e5f67890...",
│     "plan": "starter",
│     "check_limit": 10000,
│     "expiry": "2027-01-15",
│     "initialized_at": "2026-06-15T10:30:00Z",
│     "server_url": "https://guardian-ai.dev/api"
│   }
│
├── usage.json                       # Monthly check counter
│   {
│     "month": "2026-06",
│     "checks": 342,
│     "last_sync": "2026-06-15T09:30:00Z",
│     "sync_status": "success"
│   }
│
└── logs/                            # Violation & check logs (one file per day)
    ├── 2026-06-13.jsonl
    ├── 2026-06-14.jsonl
    └── 2026-06-15.jsonl             # Each line is one JSON object
        Line example:
        {"timestamp":"2026-06-15T10:30:00Z","agent_id":"support-bot",
         "type":"violation","violation_type":"pii_detected",
         "severity":"high","detail":"Aadhaar number found in input",
         "action":"blocked","model":"gpt-4","input_tokens":312,
         "cost_usd":0.0,"policy_version":"1.0"}
```

---

## 11. Database Schema (Supabase)

Only **3 tables** needed. Minimal data stored.

```sql
-- Table 1: Users (managed by Supabase Auth automatically)
-- Supabase creates this: auth.users
-- We only use: id (uuid), email, created_at

-- Table 2: License keys
CREATE TABLE licenses (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id       UUID REFERENCES auth.users(id) NOT NULL,
    key_hash      TEXT NOT NULL UNIQUE,          -- SHA-256 of the raw key
    plan          TEXT NOT NULL DEFAULT 'free',  -- 'free', 'starter', 'pro', 'enterprise'
    check_limit   INT NOT NULL DEFAULT 500,
    checks_used   INT NOT NULL DEFAULT 0,        -- synced from SDK daily
    active        BOOLEAN NOT NULL DEFAULT true,
    expiry        TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_licenses_key_hash ON licenses(key_hash);
CREATE INDEX idx_licenses_user_id ON licenses(user_id);

-- Table 3: Payments (Razorpay records)
CREATE TABLE payments (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id           UUID REFERENCES auth.users(id) NOT NULL,
    razorpay_order_id TEXT NOT NULL,
    razorpay_payment_id TEXT,
    plan              TEXT NOT NULL,              -- which plan they paid for
    amount            INT NOT NULL,               -- in paise (INR * 100)
    currency          TEXT NOT NULL DEFAULT 'INR',
    status            TEXT NOT NULL DEFAULT 'created', -- 'created', 'paid', 'failed'
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- That's it. 3 tables. No prompts. No responses. No logs.
-- We store: email, hashed key, plan type, usage count (number), payment records.
```

---

## 12. API Endpoints

### Python SDK → License Server

| Method | Endpoint | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/api/validate` | License key in body | `{ license_key, checks_used }` | `{ valid, plan, limit, expiry }` |

### Developer Portal → License Server

| Method | Endpoint | Auth | Purpose | Response |
|---|---|---|---|---|
| POST | `/api/keys` | Supabase JWT | Generate new key | `{ license_key, plan, limit }` |
| POST | `/api/billing/checkout` | Supabase JWT | Create Razorpay order | `{ order_id, amount }` |
| POST | `/api/billing/webhook` | Razorpay signature | Payment confirmation | `200 OK` |

---

## 13. Testing Strategy

```
tests/
│
├── unit/ (no network, no LLM calls, no file system)
│   │
│   ├── test_pii.py
│   │   • Test each PII pattern with valid matches
│   │   • Test false positives (regular numbers, emails vs UPI IDs)
│   │   • Test SECRET detection: HIGH confidence (12+ providers), MEDIUM (generic)
│   │   • Test secret false positives (normal text not flagged)
│   │   • Test redaction output (including [SECRET_REDACTED])
│   │   • Test .env file simulation (multi-secret detection)
│   │   • Parametrized: 50+ test cases
│   │
│   ├── test_jailbreak.py
│   │   • Test each jailbreak category (DAN, override, role-play, encoding)
│   │   • Test benign prompts return is_jailbreak=False
│   │   • Parametrized: 30+ test cases
│   │
│   ├── test_token_counter.py
│   │   • Compare against known tiktoken outputs
│   │   • Test multiple models (gpt-4, gpt-3.5)
│   │
│   ├── test_cost_calculator.py
│   │   • Test cost math for each model
│   │   • Test edge cases (0 tokens, unknown model)
│   │
│   ├── test_policy.py
│   │   • Test valid YAML loads correctly
│   │   • Test invalid YAML raises PolicyValidationError with details
│   │   • Test default agent fallback
│   │
│   ├── test_budget_manager.py
│   │   • Test allow, downgrade, block decisions
│   │   • Test session isolation
│   │
│   ├── test_tool_governor.py
│   │   • Test allowlist/denylist logic
│   │   • Test rate limiting
│   │   • Test argument validation
│   │
│   ├── test_storage.py
│   │   • Use tmp_path fixture (pytest) to mock ~/.guardian
│   │   • Test config read/write
│   │   • Test usage increment and monthly reset
│   │
│   └── test_license.py
│       • Mock httpx calls
│       • Test sync logic (>24h vs <24h)
│       • Test fail-open behavior on network error
│
├── integration/ (may use real OpenAI key from env, run with --integration flag)
│   ├── test_full_flow.py
│   │   • Load real YAML → create Guardian → complete() with mock/real LLM
│   │   • Verify analysis sheet is populated correctly
│   │
│   └── test_langchain.py
│       • Run LangChain chain with GuardianCallbackHandler
│       • Verify PII in prompt raises GuardianBlockedError
│
└── conftest.py
    Shared fixtures:
    ├── mock_openai_client — returns canned responses
    ├── sample_policy — loads policies/minimal.yaml
    ├── tmp_guardian_dir — creates temporary ~/.guardian in tmp_path
    └── pii_test_cases — parametrized PII test data
```

---

## 14. Security Model

```
WHAT GUARDIAN ACCESSES:
├── Developer's prompts → read locally, never transmitted to us
├── Developer's LLM responses → read locally, never transmitted to us
├── Developer's OpenAI API key → used locally via openai library, never read by us
└── Developer's policy YAML → read locally, never transmitted to us

WHAT WE STORE ON OUR SERVER:
├── Email (from signup)
├── Hashed license key (SHA-256, irreversible)
├── Plan type (free/starter/pro)
├── Check count (just a number, e.g., 342)
├── Expiry date
└── Payment records (Razorpay order IDs)

WHAT WE NEVER STORE:
├── Prompts
├── LLM responses
├── Violation details
├── API keys (OpenAI, Anthropic, etc.)
├── PII data
├── Log contents
└── Policy file contents

NETWORK REQUESTS GUARDIAN MAKES:
├── To OpenAI/Anthropic → developer's own LLM call (their API key)
├── To guardian-ai.dev/api/validate → once per day, { key, count } only
└── That's it. Two destinations. Nothing else. Ever.

KEY SECURITY:
├── Raw key shown to user once at signup (never retrievable again)
├── Stored hashed (SHA-256) in Supabase
├── Stored in plaintext locally at ~/.guardian/config.json
│   (same as how SSH keys work in ~/.ssh/)
├── Transmitted over HTTPS only
└── Rate limited: 10 validate calls per key per day
```

---

## 15. Dependency Map

### Python SDK: What installs when you `pip install guardian-ai`

```
guardian-ai
├── openai >= 1.0          # LLM client (wrapping OpenAI calls)
│   └── httpx              # (transitive) HTTP client
├── tiktoken >= 0.5        # Token counting
│   └── regex              # (transitive) Advanced regex
├── pyyaml >= 6.0          # YAML policy file parsing
├── pydantic >= 2.0        # Data validation for policy schema
├── httpx >= 0.25          # HTTP client for daily license sync
└── click >= 8.0           # CLI framework

Optional extras:
├── guardian-ai[presidio]  # Microsoft Presidio for NER-based PII
│   ├── presidio-analyzer
│   └── presidio-anonymizer
└── guardian-ai[langchain] # LangChain integration
    └── langchain-core >= 0.1

Dev dependencies (not shipped):
├── pytest >= 7.0
├── pytest-asyncio
├── pytest-mock
├── ruff >= 0.1
└── mypy >= 1.0
```

### Portal: What installs in the Next.js project

```
guardian-portal (Next.js)
├── next >= 14              # Framework
├── react, react-dom        # UI
├── typescript              # Language
├── @supabase/supabase-js   # Database + Auth client
├── @supabase/ssr           # Server-side Supabase for Next.js App Router
├── razorpay                # Payment gateway SDK
├── tailwindcss             # Styling
└── @tailwindcss/forms      # Form input styling
```

---

> **This document should be the first thing any contributor reads before touching code.** Every function, every data model, every API endpoint is mapped here. If it's not in this document, it's not in v1.0.
