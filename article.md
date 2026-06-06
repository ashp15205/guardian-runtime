# Why I Built a Local Firewall for AI Agents (And How "Terse Mode" Cuts My API Bill)

Autonomous coding agents like **Claude Code**, **Aider**, and **Cursor** are fundamentally changing how we build software. You can point an agent at a broken codebase, go make coffee, and come back to a perfectly refactored system. 

It’s magical. **Until it isn’t.**

As I started heavily integrating these tools into my workflow, I realized I was flying completely blind. These agents have unrestricted read access to my local file system and they talk directly to cloud LLMs (like OpenAI or Anthropic). 

This introduces two terrifying problems:

1. **The FinOps Risk:** Agents run in autonomous loops. If an agent gets stuck retrying a complex bug, it will happily burn through tokens. You can wake up to a **$100 API bill overnight** and you have zero visibility until the invoice arrives.
2. **The Security Risk:** If you accidentally leave an `AWS_SECRET_KEY` in a `.env` file, the agent will silently upload it to a third-party LLM as context. Observability tools only tell you about the leak *after* the credentials have reached the cloud.

I needed a way to control these agents *before* their requests left my machine. So, I built **Guardian Runtime**.

---

## What is Guardian Runtime?

[Guardian Runtime](https://ashp15205.github.io/guardian-runtime/) is a **local-first security middleware and FinOps firewall**. 

It runs entirely on your local machine and intercepts LLM traffic *before* it hits the internet. You just start the proxy, point your agent to `localhost:8080`, and Guardian instantly protects your infrastructure.

Here is how it solves the two biggest problems in agentic development:

### 1. Zero-Latency Secret Scanners 🔒
Guardian actively scans every single outgoing prompt for API keys, AWS credentials, and PII using regex and local ML models. 

If Claude Code tries to upload a `.env` file, Guardian **instantly drops the request locally** and returns a graceful error to the agent. The secret never touches the internet.

### 2. Hard FinOps Budgets 💸
Guardian acts as a local token ledger. You can set a strict daily budget (e.g., `$5.00/day`). If a runaway agent hits that limit, Guardian cleanly cuts off internet access to the LLM, saving your wallet.

---

## Enter "Terse Mode" 🛡️

While building the FinOps layer, I realized something: **LLMs talk way too much.**

When an autonomous agent asks an LLM for a code fix, it doesn't need polite conversational filler. It doesn't need to hear: *"Certainly! I can help you with that problem. Here is the refactored code..."* 

Output tokens are incredibly expensive (often 3x to 5x more expensive than input tokens). So, in version `1.1.0`, I introduced a feature called **Terse Mode**.

When you enable `terse_mode: true` in your Guardian policy, the engine intercepts your prompt and secretly injects a strict instruction forcing the LLM to reply in terse shorthand. No pleasantries. No transitions. Just raw, technically accurate output. 

By aggressively trimming the LLM's "mouth", Terse Mode drastically slashes your expensive output tokens while keeping the "brain" fully intact.

---

## How to Try It

Guardian Runtime is completely open-source, requires zero configuration to start, and runs locally.

**Installation:**
```bash
pip install "guardian_runtime[all]"
```

**Start the Proxy:**
```bash
guardian_runtime proxy --port 8080
```

**Use it with Claude Code:**
```bash
export ANTHROPIC_BASE_URL=http://localhost:8080
claude
```

At the end of the day, just run `guardian_runtime analytics` to see exactly how much your agents cost you and how many threats were blocked!

---

If you are building with AI agents, you need local guardrails. Check out the project below:
- 🌐 **Website:** [ashp15205.github.io/guardian-runtime](https://ashp15205.github.io/guardian-runtime/)
- 📦 **PyPI:** [pypi.org/project/guardian-runtime](https://pypi.org/project/guardian-runtime/1.1.0/)
- 💻 **GitHub:** [github.com/ashp15205/guardian-runtime](https://github.com/ashp15205/guardian-runtime)

*If you found this useful, I’d love a star on GitHub or your thoughts in the comments!*
