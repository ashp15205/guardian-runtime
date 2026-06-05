# Your AI Coding Tool Is Leaking Your Secrets. And Burning Your Budget. I Built a Fix.

Last month, Uber made headlines for blowing through their entire annual AI budget in just four months.

They had to cap every employee's AI spending mid-year.

Uber. A company with a dedicated FinOps team, engineering leadership, and budget controls most startups can only dream of.

If Uber couldn't control their AI spend, what chance do individual developers have?

---

## Two Problems. Most Tools Don't Solve Locally.

While everyone debates which LLM is smartest, two real crises are hitting developers every day.

**Crisis 1: Your secrets are leaving your machine.**

GitGuardian's State of Secrets Sprawl Report found nearly 29 million new secrets exposed in public GitHub commits in 2025 — a 34% year-over-year increase and the largest annual jump in the report's history. One API gateway, OpenRouter, saw credential leaks grow more than 48x year-over-year.

The root cause? Developers pasting files into AI tools without thinking about what's in them.

**Crisis 2: Runaway agents are destroying budgets.**

One developer reported $350 in Cursor overages in a single week. Cursor issued a public apology and refunds after the backlash. According to Gartner, agentic workflows require between 5 and 30 times more tokens per task than a standard chatbot. Developers discover this multiplier only after the bill arrives.

These aren't edge cases. They're happening to experienced developers every day.

That's why I built **Guardian Runtime**.

---

## How Easy It Is To Get This Wrong

During testing, I realized how trivially easy it is to accidentally paste a `.env` file into Claude Code.

One distracted debugging session. You grab your config for context. Somewhere in it:

```
AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE...
OPENAI_API_KEY=sk-proj-...
STRIPE_SECRET_KEY=sk_live_...
```

All of it sent to a cloud server. No warning. No scan. No filter.

And if the agent gets stuck in a retry loop verifying its own fix — which happens more than anyone admits — you wake up to a $40+ bill for a single session.

The AI tool is just a pipe. Whatever you give it, it sends. Your brain is focused on the bug, not on what's hiding in line 47 of that file you pasted.

There is still no simple local-first safety layer between developers and the LLM APIs powering these tools. I built one.
Today, Guardian Runtime already runs as a local proxy. Claude Code, Aider, and other OpenAI-compatible clients can route traffic through localhost and receive real-time protection before prompts reach the LLM provider.

---

## What Guardian Runtime Does

**Guardian Runtime** is an open-source local proxy that sits between your AI coding tool and the LLM API.

Every prompt passes through it before leaving your machine. Every response passes through it before reaching your screen. Nothing reaches OpenAI or Anthropic until Guardian clears it.

### Secrets → Blocked before they move

Before any prompt goes out, Guardian scans for:

- 🔑 **API keys & credentials** — OpenAI (`sk-proj-`), AWS (`AKIA`), GitHub (`ghp_`), Stripe, Razorpay, and generic `KEY=value` patterns
- 🆔 **Personal data** — SSNs, credit cards, Aadhaar, PAN, UPI IDs, emails, phone numbers
- 🏴‍☠️ **Jailbreak attempts** — system prompt extraction, instruction overrides, DAN variants

If something is caught, Guardian doesn't crash your tool. It returns a clean, readable message inside Claude Code or Cursor explaining exactly what was blocked. You fix it, retry, move on.

**Everything runs on your CPU. There is no Guardian cloud. The decision is made locally, in milliseconds.**

### Runaway costs → Stopped at the gate

- **Hard daily budget limit** — when your session spend hits the cap, the next request is blocked with a clear explanation. No overnight bills.
- **Token Optimizer** — strips redundant whitespace, filler text, and formatting bloat from every prompt before it hits the LLM. Fewer tokens out, smaller bill in.

```
Your Prompt
    │
    ▼
┌───────────────────────────────┐
│   GUARDIAN RUNTIME (Local)    │
│                               │
│  1. Scan secrets & PII        │──── BLOCKED → Clean error back to you
│  2. Strip token bloat         │
│  3. Enforce budget limits     │
└──────────────┬────────────────┘
               │ Only clean, lean prompts pass
               ▼
         LLM API (Cloud)
               │
               ▼
┌───────────────────────────────┐
│   GUARDIAN RUNTIME (Local)    │
│                               │
│  4. Audit the response        │──── Flags any PII in output
└──────────────┬────────────────┘
               │
               ▼
         Your Screen ✅
```

---

## Setup: 60 Seconds

```bash
pip install guardian-runtime

# Install only what you use
pip install guardian-runtime[openai]     # Cursor, Aider
pip install guardian-runtime[anthropic]  # Claude Code
```

**Claude Code:**
```bash
export ANTHROPIC_BASE_URL=http://localhost:8080
guardian_runtime proxy --port 8080
claude
```

**Aider:**
```bash
aider --openai-api-base http://localhost:8080/v1

```

> ✅ Built for Claude Code and Aider today. Cursor support in progress.

Same tools. Same workflow. Guardian is invisible when everything is clean. Loud and clear when something is wrong.

**Python SDK:**
```python
from guardian_runtime import GuardianRuntime

gr = GuardianRuntime()
response = gr.complete(
    model="gpt-4o",
    messages=[{"role": "user", "content": user_input}]
)

if response.blocked:
    print(f"🛡 Blocked: {response.violations[0].detail}")
else:
    print(response.content)
```

---

## Why Every Other "AI Security" Tool Gets This Wrong

Every solution I found before building Guardian scans your prompts by routing them through *their* cloud server first.

You're protecting your secrets from OpenAI by sending them to someone else's infrastructure instead. That's not security. That's moving the risk.

Guardian never receives your data. The scan runs entirely on your machine — pattern matching with optional Microsoft Presidio ML models if you want them. If a request is blocked, the decision happened on your CPU. Nothing left your machine.

Zero telemetry. Zero accounts. Zero signups. MIT licensed. Every line of code is on GitHub.

---

## The Design Principle That Made This Actually Usable

Early versions were too aggressive. Regular emails got flagged as PII. Variable names that looked like keys got blocked. False positives everywhere.

Security tools that are annoying get disabled. That's not a theory — that's what happens.

So detection was rebuilt with a two-tier confidence system. High confidence hits — known prefixes like `AKIA`, `sk-proj-`, `ghp_` — block immediately. Medium confidence patterns get flagged but stay overrideable. Common patterns like `user@gmail.com` are explicitly excluded.

The design principle that fixed everything:

**The threat isn't a malicious attacker. The threat is a distracted developer who just wants to fix their bug.**

That one shift changed how every part of Guardian works.

---

## Get It

Free. No tiers. No rate limits. No paywall. Ever.

🌐 **Docs:** [https://ashp15205.github.io/guardian-runtime/](https://ashp15205.github.io/guardian-runtime/)
⭐ **GitHub:** [https://github.com/ashp15205/guardian-runtime](https://github.com/ashp15205/guardian-runtime)
📦 **Install:** `pip install guardian-runtime`

PRs welcome. Issues welcome. This is a community project.

---

*One GitHub star is the only thing I'll ever ask for.*

*— Ashish Patil*

---

*Sources: GitGuardian State of Secrets Sprawl 2025 · Gartner March 2026 · TechCrunch (Uber AI spending cap, June 2026) · Morph AI Coding Costs 2026 · CloudZero State of AI Costs*