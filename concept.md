# Guardian Runtime: Concept & Product Vision

## The Problem
As AI coding agents (like Claude Code, Cursor, and Aider) become deeply integrated into developer workflows, they introduce two massive, unmanaged risks:
1. **The Cost Risk (Runaway Spend):** Autonomous agents can get stuck in infinite loops or parse massive, irrelevant files. Without warnings, developers can wake up to hundreds of dollars in API bills. There is currently zero visibility into session costs until the bill arrives at the end of the month.
2. **The Security Risk (Secret Leaks):** These agents have unrestricted read access to your local workspace. If you accidentally leave an `AWS_SECRET_KEY` in a configuration file, or have sensitive customer PII in a `.csv` file, the agent will silently upload it to a third-party LLM provider over the public internet.

## What is Guardian Runtime?
Guardian Runtime is a **Zero-Latency FinOps & Security Firewall for AI Applications**. 
It operates entirely on your local machine to intercept, scan, optimize, and log LLM traffic *before* it hits external APIs like OpenAI or Anthropic.

Instead of paying for expensive third-party enterprise firewalls that add 200ms of network latency to every request, Guardian Runtime runs natively on your machine (`localhost`), ensuring complete data privacy and lightning-fast execution.

## How it Solves the Problem
Guardian Runtime acts as an intermediary. When your CLI agent tries to send a prompt to OpenAI:
1. The agent sends the request to Guardian Runtime (running on `localhost:8080`).
2. Guardian strips out bloated whitespace (**Token Optimizer**).
3. Guardian scans the prompt for API keys, AWS credentials, and PII (**Secret Firewall**).
4. Guardian checks if you have exceeded your daily dollar limit (**FinOps**).
5. If the prompt is safe, Guardian forwards it to the actual LLM (OpenAI/Anthropic).
6. Guardian intercepts the response, audits it, and streams it back to the agent seamlessly.

If a threat or budget limit is detected, Guardian instantly blocks the request, saving you money and protecting your data without ever establishing an outbound network connection.

## Key Features

### 1. ML-Powered Secret & PII Firewall
Guardian uses a two-tier confidence engine. It utilizes blazing-fast Regex for detecting known secret patterns (like `sk-proj-...` or `AKIA...`). For complex natural language, it lazy-loads **Microsoft Presidio** to perform highly-accurate ML-based NLP scanning for Emails, Phone Numbers, SSNs, and Credit Cards.

### 2. Hard Local Budgets
Configure a strict daily budget (e.g., $10.00). Guardian tracks every token consumed across all your local CLI tools. If an agent goes rogue and tries to spend $11, Guardian cuts the connection immediately.

### 3. High-Concurrency Local Proxy
A built-in threadpool proxy server lets you intercept traffic from any tool without modifying its source code. Because it uses asynchronous threadpools (`starlette.concurrency`), it can handle hundreds of simultaneous requests from multiple agents with zero event-loop blocking.

### 4. Jailbreak & Unsafe Command Defense
Pattern-matched detection for DAN (Do Anything Now) variants, instruction overrides, and system prompt extraction attempts. It stops adversarial prompts from hijacking your agent before the LLM even sees them.

### 5. Token Optimizer
Automatically trims redundant tokens, conversational filler, and excessive whitespace from automated agent prompts, passively reducing your API bills by 10-15%.

### 6. Graceful Upstream Error Handling
If the OpenAI or Anthropic APIs go down mid-stream, Guardian gracefully intercepts the crash and streams a clean `[GUARDIAN_RUNTIME ERROR] Upstream Provider Offline` message back to the agent. This prevents your terminal bots from abruptly crashing with HTTP 500 errors.

### 7. Beautiful Local Dashboard
All intercepted threats, session analytics, and cost data are stored locally in `~/.guardian_runtime/`. Guardian ships with a gorgeous, dark-mode offline dashboard so you can visualize your usage and security blocks in real time.

## Target Audience
- **Solo Developers & Freelancers** who want to use autonomous coding agents without fearing a massive API bill at the end of the month.
- **Security-Conscious Engineers** working on enterprise codebases who cannot risk an AI agent leaking proprietary AWS keys or `.env` files.
- **AI Builders** building local multi-agent systems who need a transparent, fast, and local observability layer.
