# Why I Built a Local Firewall for My AI Agents

*How to stop autonomous coding tools from leaking your AWS keys and burning your API budgets.*

It's 2:00 AM. You've asked Claude Code to refactor your authentication module while you grab coffee.

You come back 20 minutes later. The agent got stuck in a recursive loop fixing a syntax error. It retried 400 times. You just burned $85 of API budget.

Then you check the logs. It ingested your `.env.local` for context. Your production `AWS_SECRET_ACCESS_KEY` was sent, in plaintext, to Anthropic's servers.

If you build with AI agents, you've felt some version of this panic. We give these tools autonomous access to our codebases — but have zero control over what they actually send over the network.

That's exactly why I built **Guardian Runtime**.

*Guardian Runtime acts as an intercept proxy, showing you exactly what your agents are sending and blocking threats in real-time.*

---

## The Dual Threat of Autonomous AI

Modern AI coding agents introduce two risks that traditional security tools weren't built to handle:

### 1. The FinOps Risk: Infinite Loops
When an agent hits a failing test, it retries. And retries. And retries. With a 100,000-token context window, every retry costs real money. A simple bug spirals into a massive bill because there's no hard spending limit on the agent itself.

### 2. The Security Risk: Silent Secret Leaks
Agents need broad context to work. They read your entire workspace. If an engineer leaves a Stripe key or a database password anywhere in the codebase, the agent silently scoops it up and sends it to OpenAI or Anthropic's servers — a serious security and compliance risk.

---

## Guardian Runtime: A Local AI Firewall

We can't rely on LLM providers to solve this. We can't modify the source code of proprietary tools.

We need a middleman.

[Guardian Runtime](https://ashp15205.github.io/guardian-runtime/) is an open-source, local HTTP proxy that sits between your AI tools and the internet. Every prompt passes through it before leaving your machine. Every response passes through it before reaching your screen.

### How it works

Instead of pointing your tools at Anthropic or OpenAI directly, you point them at Guardian on localhost. When your agent makes an API call, Guardian intercepts it and runs two checks:

**1. Secret & PII Scanning**
Guardian scans the outgoing prompt locally using pattern matching and optional Microsoft Presidio ML models. If it detects an AWS key, a credit card number, or personal data — it drops the request instantly. The agent receives a clean explanation of what was blocked. Nothing left your machine.

**2. Hard Budget Limits**
Guardian calculates the exact token cost of the request *before* it's sent using `tiktoken`. If it pushes you over your daily limit, the request is blocked. No surprise bills.

---

## Zero Configuration Required

```bash
# Install
pip install "guardian-runtime[anthropic]"

# Start the firewall
guardian_runtime proxy --port 8080

# Point Claude Code at it
export ANTHROPIC_BASE_URL=http://localhost:8080
claude
```

Done. No API keys, no cloud accounts, no YAML files to start.

> ✅ Fully supported: Claude Code, Aider. Cursor support in progress.

To see exactly what was intercepted and what you've spent:
```bash
guardian_runtime analytics
```

---

## Taking Back Control

The future of software is autonomous agents. But autonomy without governance is a security breach waiting to happen.

Guardian Runtime is free, open-source, and runs entirely on your machine. Your logs never leave your laptop.

If you're building with AI agents — take 60 seconds to lock down your environment.

👉 **GitHub:** [ashp15205/guardian-runtime](https://github.com/ashp15205/guardian-runtime)
👉 **Install:** `pip install guardian-runtime`