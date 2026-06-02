# Guardian Runtime — 16-Week Execution Plan

**Builder:** Final-year CS student, Pune, India  
**Commitment:** 2–3 hours/day (14–21 hrs/week)  
**Timeline:** June 2, 2026 → September 21, 2026  
**Goal:** Local-first Python SDK on PyPI, first paying users via license keys, ProductHunt launch

> **June sprint:** Ship **v1.0.0** by **Jun 30, 2026** (full engine + guards + CLI). Day-by-day plan: **[V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md)**.  
> **Done:** [guardian-runtime 0.1.1 on PyPI](https://pypi.org/project/guardian-runtime/) (Jun 1, 2026) — PII/secrets, policy schema.

---

## Timeline Summary

| Phase | Weeks | Dates | Goal | Milestone |
|---|---|---|---|---|
| **Phase 0 — Thinking** | 1–2 | Jun 2 – Jun 15 | Validation, scope lock on local-first model | ✅ Problem validated, scope locked |
| **Phase 0.5 — v1 Sprint** | — | Jun 2 – Jun 30 | Full runtime pipeline + 1.0.0 launch | 🔄 See [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md) |
| **Phase 1 — Core SDK** | 3–6 | Jun 16 – Jul 13 | Guards, YAML engine, local storage | ✅ PyPI 0.1.1; **1.0.0 by Jun 30** |
| **Phase 2 — First Users** | 7–9 | Jul 14 – Aug 3 | Outreach, bug fixes, real local usage | ✅ 5 real users running Guardian |
| **Phase 3 — Auth & Billing**| 10–13| Aug 4 – Aug 31 | License key server, Next.js portal, Razorpay | ✅ Key server deployed, billing live |
| **Phase 4 — Launch** | 14–16 | Sep 1 – Sep 21 | ProductHunt, HackerNews, IndiaAI grant | ✅ Public launch, 100+ GitHub stars |

---

## Free Tools & APIs Used

| Tool | Purpose | Cost |
|---|---|---|
| **GitHub** | Code hosting, CI/CD | Free |
| **PyPI** | Python package distribution | Free |
| **Supabase** (free tier) | Key validation DB, Auth for portal | Free |
| **Vercel** (free tier) | License portal hosting (Next.js) | Free (hobby tier) |
| **tiktoken** | OpenAI token counting library | Free (MIT) |
| **Presidio** (Microsoft) | PII detection NER models | Free (MIT) |
| **Razorpay** (test mode) | Indian payment gateway | Free for testing |

---

## The One Rule

> **Talk to a real user every week.**
>
> Your main pitch is: *"Are you afraid of sending your LLM logs to a cloud observability tool? We built a local-first governance layer. The data never leaves your machine."* Pitch globally: Hacker News, Reddit (r/LocalLLaMA, r/MachineLearning), dev Twitter/X, LangChain/discord, and local meetups (Pune, etc.).

---

## Phase 0 — Thinking (Week 1–2)

### Week 1: Problem Validation (Jun 2 – Jun 8)
**Goal:** Validate that companies want *local* governance.
- **Mon-Wed:** Setup GitHub repo. DM 10 people on Twitter about local-first privacy.
- **Thu-Sun:** Conduct 2 user interviews focusing on data privacy concerns with existing tools (Langfuse/LangSmith). Read up on the India DPDP Act.

### Week 2: Scope Lock & Architecture (Jun 9 – Jun 15)
**Goal:** Lock the v0.1 scope around local-first execution.
- **Scope:** Input Guard (PII/Jailbreak), Output Guard, Cost tracking.
- **Architecture:** `~/.guardian/config.json` for license keys, `~/.guardian/usage.json` for counts. Zero cloud logging.
- **CI/CD:** Setup pytest and GitHub Actions.

---

## Phase 1 — Core SDK (Week 3–6)

### Week 3: PII Detection, Secret Scanning & Policy Engine (Jun 16 – Jun 22)
- ✅ Build regex-based PII detector (SSN, Aadhaar, PAN, UPI).
- ✅ Build secret/credential detector (OpenAI `sk-`, AWS `AKIA`, GitHub `ghp_`, Stripe, Razorpay, Groq + generic KEY=value patterns).
- ✅ Build YAML parser using Pydantic models.
- ✅ Unit tests; ✅ PyPI [0.1.1](https://pypi.org/project/guardian-runtime/).
- **Remaining for v1.0:** Input/Output guards, engine, CLI — see [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md).

### Week 4: Jailbreak Detection & Token Counting (Jun 23 – Jun 29)
- Build jailbreak keyword/pattern matching.
- Wrap `tiktoken` for local token counting.
- Integrate into `InputGuard`.

### Week 5: Output Guard & Hallucination Detection (Jun 30 – Jul 6)
- Implement LLM-as-judge hallucination checks using LiteLLM for "Bring Your Own Model" (BYOM) support (OpenAI, Anthropic, Ollama).
- Build local JSONL logger (`guardian/logging/local.py`) instead of cloud logging.

### Week 6: License Key Management & CLI (Jul 7 – Jul 13)
**Goal:** Build the local-first storage manager and CLI.
- Build `guardian/cli/init.py` for `guardian init --key`.
- Build `guardian/core/storage.py` to write/read `~/.guardian/config.json` and track monthly check counts in `usage.json`.
- Publish v0.1.0 to PyPI!

**Local Storage Implementation:**
```python
# guardian/core/storage.py
import json
import os
from pathlib import Path
from datetime import datetime

GUARDIAN_DIR = Path.home() / ".guardian"
CONFIG_FILE = GUARDIAN_DIR / "config.json"
USAGE_FILE = GUARDIAN_DIR / "usage.json"

class LocalStorage:
    @staticmethod
    def save_license(key: str, plan: str = "free"):
        GUARDIAN_DIR.mkdir(exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"license_key": key, "plan": plan}, f)

    @staticmethod
    def increment_usage():
        # Track checks locally. Synced to server once daily.
        today = datetime.now().strftime("%Y-%m")
        usage = {"month": today, "checks": 0, "last_sync": None}
        
        if USAGE_FILE.exists():
            with open(USAGE_FILE, "r") as f:
                usage = json.load(f)
                if usage["month"] != today:
                    usage = {"month": today, "checks": 0, "last_sync": None}
        
        usage["checks"] += 1
        with open(USAGE_FILE, "w") as f:
            json.dump(usage, f)
```

---

## Phase 2 — First Users (Week 7–9)
- **Week 7:** Build LangChain integration. Write blog: "Why Observability Is Not Enough for AI in Production (And Why It Should Be Local)".
- **Week 8:** Fix bugs, add more PII patterns. Reach 5 active developers using it locally.
- **Week 9:** Build FinOps budget features (local tracking of spend).

---

## Phase 3 — License Server & Billing (Week 10–13)
**Note:** We are NOT building a dashboard to view logs (because logs are local). We are building a developer portal to purchase plans and generate license keys.

### Week 10: Developer Portal Foundation (Aug 4 – Aug 10)
- Initialize Next.js project. Setup Supabase Auth.
- Build signup flow. Give every new user a "Free" tier license key automatically.

### Week 11: License API Server (Aug 11 – Aug 17)
- Build the `/api/validate` endpoint on Next.js.
- This endpoint takes `{ key, checks_used }` and returns `{ valid: true, limit: 10000 }`.
- Update the Python SDK to ping this URL once daily.

### Week 12 & 13: Razorpay Integration (Aug 18 – Aug 31)
- Integrate Razorpay for "Starter" and "Pro" plans.
- Upon successful payment, upgrade their license key in the Supabase DB.

**Razorpay & License Key Generation:**
```tsx
// app/api/billing/create-subscription/route.ts
import { NextRequest, NextResponse } from "next/server";
import Razorpay from "razorpay";
import { createServerClient } from "@/lib/supabase";
import crypto from "crypto";

const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID!,
  key_secret: process.env.RAZORPAY_KEY_SECRET!,
});

export async function POST(req: NextRequest) {
  const { planId, userId } = await req.json();
  const supabase = createServerClient();

  // Create subscription
  const subscription = await razorpay.subscriptions.create({
    plan_id: "plan_pro_monthly",
    total_count: 12,
  });

  // Generate unique license key (gdn_live_xxxx)
  const licenseKey = `gdn_live_${crypto.randomBytes(16).toString("hex")}`;

  // Store hashed key in DB to upgrade user tier
  await supabase.from("licenses").insert({
    user_id: userId,
    key_hash: crypto.createHash("sha256").update(licenseKey).digest("hex"),
    plan: "pro",
    limit: 100000,
    active: true
  });

  return NextResponse.json({
    subscription_id: subscription.id,
    license_key: licenseKey // Shown to user ONCE
  });
}
```

---

## Phase 4 — Launch (Week 14–16)

### Week 14: Pre-Launch Polish (Sep 1 – Sep 7)
- Write documentation site (MkDocs). Emphasize "Local-First Architecture".
- Record a demo video showing `guardian init --key` and local log tracking.

### Week 15: ProductHunt & Hacker News Launch (Sep 8 – Sep 14)
**ProductHunt Copy:**
```
Tagline: Local-first AI governance. Your data stays yours.

Description:
Guardian Runtime is an open-source middleware that sits between your 
AI application and any LLM. 

Unlike existing observability tools that require you to send your highly sensitive 
prompts to their cloud, Guardian runs 100% on your local machine.

• Prompts, responses, and violations NEVER leave your infrastructure
• Block PII natively (GDPR, HIPAA, India DPDP Act)
• Catch exposed API keys (OpenAI, AWS, GitHub, Stripe) before they reach any LLM
• Catch hallucinations and jailbreaks before they happen
• Daily sync only sends your license key and a usage count number

Privacy by design. 3 lines of code to integrate.
```

### Week 16: IndiaAI Grant & Growth (Sep 15 – Sep 21)
- Apply for IndiaAI Mission grant, emphasizing that Guardian enables DPDP compliance without data leaving Indian sovereign boundaries.
- Contact Enterprise companies for offline-license pilots.

---

## Key Metrics to Track
- PyPI downloads (Target: 500+)
- Active License Keys synced (Target: 50+)
- Razorpay subscriptions (Target: 2+)
- GitHub stars (Target: 100+)
