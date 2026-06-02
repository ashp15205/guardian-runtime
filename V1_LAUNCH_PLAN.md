# Guardian Runtime — v1.0 Launch Plan

**Target launch:** June 30, 2026  
**Today’s release:** [0.1.1 on PyPI](https://pypi.org/project/guardian-runtime/) (published Jun 1, 2026)  
**Next release:** `1.0.0` — first **runtime governance** product (not just scanners)  
**Effort budget:** 2–3 hours/day (~60–85 hours remaining in June)

---

## 1. Executive summary

Guardian Runtime is a **local-first SDK** that sits between your app and any LLM. The **vision** is:

```
User Input → [Input Guard] → LLM → [Output Guard] → User
                    ↓                      ↓
              local JSONL logs (~/.guardian/logs/)
```

**Where we are:** Detectors and policy schema are shipped on PyPI. The **orchestration layer** (engine, guards, CLI, logging) is not built yet.

**Where we’re going (v1.0):** A developer installs `guardian-runtime`, loads a YAML policy, and calls `Guardian.complete()` — PII, secrets, and jailbreaks are blocked **before** the LLM sees them; output is scanned **before** the user sees it. No prompts uploaded to Guardian’s servers.

**Audience:** Developers, firms, and enterprises **worldwide**. Compliance spans GDPR, HIPAA, CCPA, SOC2-minded deployments, plus India DPDP identifiers (Aadhaar, PAN, UPI) as a depth differentiator — not a geographic limit.

---

## 2. June launch goals — what we ship & why

**Launch date:** June 30, 2026 → **`guardian-runtime 1.0.0` on PyPI**

**One sentence:** The first version developers can **wrap an OpenAI call** in 3 lines and get **runtime blocking + local logs** — not just manual scanners.

### 2.1 Launch goals (outcomes)

| # | Goal | Why it matters |
|---|------|----------------|
| G1 | **Working `Guardian.complete()`** | This *is* the product. Without it, PyPI is a utility library, not governance middleware. |
| G2 | **Block threats before the LLM** | Core promise vs Langfuse/LangSmith — stop leaks *before* OpenAI sees them, not after. |
| G3 | **Block leaks on the way out** | PII/secrets in model output still reach users today; output guard closes the loop. |
| G4 | **Policy in YAML, zero code changes** | Teams tune rules without redeploying; enterprise-friendly ops model. |
| G5 | **100% local — no prompt upload** | Trust wedge for regulated teams (finance, health, gov) globally. |
| G6 | **CLI + example + PyPI 1.0** | Any developer worldwide can install and run in &lt;5 minutes. |
| **OpenAI + Gemini (v1)** | Two providers; Gemini free tier for testing |

### 2.2 Features to implement in June (v1.0.0)

| Feature | What it does | Why in v1 (not later) |
|---------|--------------|------------------------|
| **GuardianEngine** | Orchestrates full request/response pipeline | Without engine, nothing connects — #1 blocker |
| **Input Guard** | Runs PII + secrets + jailbreak on user prompt | Uses detectors already shipped; delivers “firewall” story |
| **Output Guard** | Runs PII + secrets on LLM response | Prevents model from echoing sensitive data to user |
| **Jailbreak detector** | 30–50 regex patterns (DAN, ignore instructions, etc.) | Security table-stakes for any governance product |
| **OpenAI wrapper** | `chat.completions` via `OPENAI_API_KEY` | Paid production use |
| **Gemini wrapper** | `google-generativeai` via `GEMINI_API_KEY` | Free-tier testing & global devs |
| **Local JSONL logs** | Violations at `~/.guardian/logs/` | Audit trail without cloud; proves local-first |
| **CLI** (`init`, `validate`, `status`, `logs`) | Setup, policy check, usage, log viewer | Developers expect a CLI; validates policy without writing code |
| **Local storage** | `~/.guardian/config.json`, `usage.json` | Foundation for limits and license sync later |
| **Offline license tier** | Works without server; optional `GUARDIAN_LICENSE_URL` | Don’t block launch on portal/billing (August) |
| **Token count + cost estimate** | tiktoken count + USD estimate in response metadata | Teams see cost per call; prompt length → token awareness |
| **Max input tokens (optional policy cap)** | Block or reject if prompt exceeds N tokens | Lightweight FinOps — prevents runaway context bills |
| **Tests (≥80) + CI** | pytest + ruff on 3.9–3.12 | Credibility for OSS and enterprise evaluators |
| **`examples/quickstart.py`** | Copy-paste OpenAI + policy demo | Reduces time-to-first-block for new users |

### 2.3 Not in June (and why we defer)

| Deferred | Why wait |
|----------|----------|
| Anthropic, Azure, Ollama | v1.1 — LiteLLM-style router |
| OpenAI + Gemini | ✅ v1 |
| Hallucination judge | Extra LLM call + BYOM complexity |
| LangChain / CrewAI | Integration layer after core pipeline works |
| Smart token optimization (summarize/trim history) | Harder than count + cap; v1.1 |
| Budget hard-stop + model downgrade | Needs budget manager + router |
| Tool governor / agent loops | Agentic scope; post-v1 |
| Portal, Razorpay, paid tiers | Monetization in Aug–Sep per [PLAN.md](./PLAN.md) |

### 2.4 June success = developers can say this

> “I pip-installed Guardian, dropped a YAML policy, wrapped my OpenAI call, and it blocked a jailbreak and an Aadhaar leak — nothing left my machine.”

---

## 3. Current status — detailed

### 3.1 What works today (v0.2.0 dev)

| Capability | Status |
|------------|--------|
| `Guardian.complete()` + OpenAI | ✅ |
| Input/Output guards | ✅ |
| Jailbreak detector (~40 patterns) | ✅ |
| CLI: init, validate, status, logs | ✅ |
| Local storage + JSONL logs | ✅ |
| Token count, cost estimate, `max_input_tokens` | ✅ |
| PII/secrets scanners | ✅ |
| Policy YAML | ✅ |
| Tests + CI | ✅ 92 tests |
| PyPI | ✅ 0.1.1 published; **1.0.0** at June launch |

```python
from guardian import Guardian

guardian = Guardian.from_policy("policies/minimal.yaml")
# Requires OPENAI_API_KEY for live LLM calls
response = guardian.complete(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### 3.2 Still deferred (post–1.0.0 or July)

| Capability | Target |
|------------|--------|
| Hallucination judge | v1.1 (Jul) |
| Anthropic / LiteLLM multi-provider | v1.1 |
| LangChain callback | v1.1 |
| Budget hard-stop + model downgrade | v1.1 |
| Portal + Razorpay billing | Aug–Sep |

### 3.3 Repository inventory

```
guardian/
├── core/engine.py, storage.py, license.py, models.py  ✅
├── guards/input_guard.py, output_guard.py             ✅
├── guards/validators/pii.py, jailbreak.py               ✅
├── finops/token_counter.py, cost_calculator.py        ✅
├── logging/local.py                                     ✅
└── cli/init.py, validate.py, status.py, logs.py       ✅

tests/integration/test_full_flow.py                      ✅
examples/quickstart.py                                   ✅
.github/workflows/ci.yml                                 ✅
```

### 3.4 Product read

**v0.2.0 dev** delivers the core runtime product. **June 1.0.0 launch** = PyPI tag, README/demo polish, and beta user validation — not major new features.

---

## 4. v1.0.0 definition — what “launch” means

### 4.1 v1 product promise

> Install Guardian. Point it at a YAML policy. Wrap your OpenAI call. Sensitive data and jailbreaks never reach the model; violations are logged locally. Your prompts never touch our servers.

### 4.2 In scope for 1.0.0 (must ship by Jun 30)

| # | Feature | Acceptance criteria |
|---|---------|---------------------|
| 1 | **GuardianEngine.complete()** | Full pipeline; returns content or blocked response |
| 2 | **Input Guard** | PII + secrets + jailbreak per policy flags |
| 3 | **Output Guard** | PII + secrets on LLM response |
| 4 | **OpenAI integration** | `chat.completions.create` with developer’s `OPENAI_API_KEY` |
| 5 | **Policy-driven** | Per-agent rules from YAML; `load_policy()` wired |
| 6 | **Local JSONL logs** | Violations at `~/.guardian/logs/YYYY-MM-DD.jsonl` |
| 7 | **CLI** | `init`, `validate`, `status`, `logs` |
| 8 | **Local storage** | `~/.guardian/config.json`, `usage.json` |
| 9 | **License (offline)** | Free tier works without server; `GUARDIAN_LICENSE_URL` optional |
| 10 | **FinOps lite** | Token count + cost estimate + optional max-input-tokens cap |
| 11 | **Tests + CI** | ≥80 tests; GitHub Actions on Python 3.9–3.12 |
| 12 | **Docs + example** | README integration section; `examples/quickstart.py` |
| 13 | **PyPI 1.0.0** | Tagged release + CHANGELOG |

### 4.3 Explicitly out of scope (v1.1+, July onward)

- Hallucination judge (requires extra LLM call)
- Tool governor, agent loop detection, automatic model downgrade
- LangChain / CrewAI callbacks (stretch only if Week 4 has slack)
- Presidio optional NER pack
- Next.js portal, Supabase, Razorpay billing
- ProductHunt / paid tiers (September per [PLAN.md](./PLAN.md))

### 4.4 Target developer experience (v1.0)

```python
from guardian import Guardian

guardian = Guardian.from_policy("policies/minimal.yaml")

response = guardian.complete(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": user_input}],
)

if response.blocked:
    print(response.violation.type)   # e.g. AADHAAR, JAILBREAK, SECRET
else:
    print(response.content)
```

```bash
guardian init --key gdn_free_xxxxx      # optional
guardian validate policies/minimal.yaml
guardian status
guardian logs --tail 20
```

---

## 5. Gap analysis: 0.1.1 → 1.0.0

| Layer | 0.1.1 | 1.0.0 | Effort |
|-------|-------|-------|--------|
| Detectors | Done | Wire into guards | Low |
| Policy schema | Done | Wire into engine | Low |
| Guards | Missing | Build input + output | Medium |
| Engine | Stub | Full pipeline | **High** |
| OpenAI client | Missing | Add to engine | Medium |
| Logging | Missing | JSONL module | Low |
| Storage + license | Stub | Offline-first impl | Medium |
| Jailbreak | Stub | 30–50 patterns | Medium |
| FinOps | Stub | tiktoken + price table | Low |
| CLI | Empty | 4 commands | Medium |
| Tests | ~39 | 80+ incl. integration | Medium |
| CI + examples | Missing | Add both | Low |

**Estimated build order:** models → guards → jailbreak → engine → logging/storage → CLI → tests → launch.

---

## 6. Implementation plan — June 2026

### Phase A — Week 1 (Jun 2–8): Guards & foundations

**Goal:** Text flows through input/output guards without calling OpenAI.

| Priority | Task | Files | Done when |
|----------|------|-------|-----------|
| P0 | Core data models | `guardian/core/models.py` | `GuardResult`, `GuardianResponse`, `Violation` |
| P0 | Input Guard | `guardian/guards/input_guard.py` | Reads policy; runs PII, secrets, jailbreak |
| P0 | Jailbreak detector | `guardian/guards/validators/jailbreak.py` | 30–50 patterns; `test_jailbreak.py` |
| P0 | Output Guard | `guardian/guards/output_guard.py` | Scans LLM response text |
| P1 | FinOps lite | `finops/token_counter.py`, `cost_calculator.py` | Unit tests pass |
| P1 | Engine (partial) | `core/engine.py` | Input guard + block path only |
| P2 | User feedback | — | 1 interview; tune false positives |

**Week 1 exit:** `InputGuard.check(text, agent_id)` blocks Aadhaar, `sk-...`, and a DAN-style jailbreak.

---

### Phase B — Week 2 (Jun 9–15): Engine & OpenAI

**Goal:** End-to-end governed LLM call works locally.

| Priority | Task | Files | Done when |
|----------|------|-------|-----------|
| P0 | OpenAI in engine | `core/engine.py` | Mocked integration test |
| P0 | Output guard after LLM | `core/engine.py` | Blocked if PII in response |
| P0 | Local logger | `guardian/logging/local.py` | JSONL append per violation |
| P0 | Local storage | `core/storage.py` | config + usage JSON |
| P1 | License manager | `core/license.py` | Offline free tier; optional sync URL |
| P1 | Wire `Guardian` class | `__init__.py` | `from_policy().complete()` works |
| P1 | Integration test | `tests/integration/test_full_flow.py` | Mock OpenAI, full pipeline |
| P2 | Dogfood | — | Run with real API key; fix bugs |

**Week 2 exit:**

```python
Guardian.from_policy("policies/minimal.yaml").complete(model="gpt-4o-mini", messages=[...])
```

---

### Phase C — Week 3 (Jun 16–22): CLI, CI, polish

**Goal:** Another developer can install and use Guardian in under 10 minutes.

| Priority | Task | Files | Done when |
|----------|------|-------|-----------|
| P0 | CLI init + validate | `cli/init.py`, `validate.py` | Registered in `main.py` |
| P0 | CLI status + logs | `cli/status.py`, `logs.py` | Reads `~/.guardian/` |
| P0 | Quickstart example | `examples/quickstart.py` | Copy-paste runnable |
| P0 | Production policy | `policies/production.yaml` | Sensible defaults |
| P0 | GitHub Actions CI | `.github/workflows/ci.yml` | pytest + ruff, 3.9–3.12 |
| P1 | Expand test suite | `tests/unit/test_*.py` | ≥80 tests total |
| P1 | `GuardianBlockedError` | `core/models.py` or `exceptions.py` | Clear DX on block |
| P2 | Internal beta | — | 3 external users try quickstart |

**Week 3 exit:** `pip install -e .` → `guardian validate` → `python examples/quickstart.py` works.

---

### Phase D — Week 4 (Jun 23–30): Launch

**Goal:** Public v1.0.0 on PyPI with announcement.

| Date | Task |
|------|------|
| **Jun 23** | README: v1 integration guide, limitations, compliance disclaimer |
| **Jun 24** | CHANGELOG 1.0.0; bump `pyproject.toml` to `1.0.0`; classifier → Beta/Production |
| **Jun 25** | `twine check`; test install in clean venv |
| **Jun 26** | Git tag `v1.0.0`; PyPI publish; GitHub Release notes |
| **Jun 27** | 2–3 min demo: block Aadhaar + secret + jailbreak |
| **Jun 28** | Launch: Show HN, r/LocalLLaMA, dev Twitter/X, LangChain/discord |
| **Jun 29** | Monitor issues; ship `1.0.1` hotfix if P0 |
| **Jun 30** | Retrospective; open v1.1 GitHub milestones |

**Feature freeze:** Jun 23 — no new scope after this date, polish only.

---

## 7. Engine pipeline (v1 reference)

```
GuardianEngine.complete(model, messages, agent_id, session_id)
│
├─ 1. license.check_or_sync()          # offline OK if no URL
├─ 2. storage.check_usage_limit()      # free tier: 10k checks/mo
├─ 3. input_guard.check(user_text)     # PII → secrets → jailbreak
│      └─ if blocked → log → return GuardianResponse(blocked=True)
├─ 4. openai.chat.completions.create() # developer's API key
├─ 5. output_guard.check(response)    # PII + secrets on output
│      └─ if blocked → log → return GuardianResponse(blocked=True)
├─ 6. finops.record_tokens()           # metadata only in v1
├─ 7. storage.increment_usage()
├─ 8. logger.write_jsonl(violation_or_check)
└─ 9. return GuardianResponse(content=..., metadata={tokens, cost})
```

---

## 8. Files to create or complete

### Must create (new)

```
guardian/core/models.py
guardian/guards/input_guard.py
guardian/guards/output_guard.py
guardian/logging/local.py
guardian/logging/__init__.py
guardian/cli/init.py
guardian/cli/validate.py
guardian/cli/status.py
guardian/cli/logs.py
examples/quickstart.py
policies/production.yaml
tests/unit/test_jailbreak.py
tests/unit/test_input_guard.py
tests/unit/test_output_guard.py
tests/unit/test_storage.py
tests/integration/test_full_flow.py
.github/workflows/ci.yml
```

### Must complete (stubs → working)

```
guardian/core/engine.py
guardian/core/storage.py
guardian/core/license.py
guardian/guards/validators/jailbreak.py
guardian/finops/token_counter.py
guardian/finops/cost_calculator.py
guardian/cli/main.py          # register subcommands
```

### Leave as-is for v1 (no-op or deferred)

```
guardian/guards/validators/hallucination.py   → v1.1; policy flag logs warning if enabled
portal/                                       → Aug–Sep
```

---

## 9. Parallel workstreams

| Stream | June actions |
|--------|--------------|
| **Engineering** | Follow Phases A–D; critical path = engine + guards |
| **QA** | False-positive cases (emails in code, test card numbers); never log raw secrets |
| **Docs** | Keep README honest; ARCHITECTURE status table updated at v1 |
| **GTM (global)** | 2 builder interviews/week; 3 beta users before Jun 22 |
| **Release** | PyPI 1.0.0 Jun 26; optional TestPyPI dry-run Jun 25 |
| **Legal** | Apache-2.0; README: “assistive compliance tool, not legal advice” |

---

## 10. Success metrics (Jun 30)

| Metric | Target |
|--------|--------|
| `Guardian.complete()` works with OpenAI | ✅ |
| PyPI `guardian-runtime==1.0.0` | Published |
| Unit + integration tests | ≥80, all green |
| CLI commands | 4 working |
| External beta users | ≥3 tried quickstart |
| Open P0 bugs | 0 |
| README install → first block | <5 minutes |

---

## 11. Risks & fallbacks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Engine takes longer than Week 2 | Medium | Cut finops metadata; ship block path first |
| Jailbreak false positives | Medium | `jailbreak_detection: false` in policy; add FLAG mode |
| Behind schedule by Jun 20 | Medium | Output guard → redact-only; still ship 1.0.0 |
| Scope creep (LangChain, portal) | High | **Hard no** until Jul 1 |
| PyPI description ≠ code | Low | Sync README before 1.0.0 publish |

---

## 12. Launch checklist

**Code**
- [ ] Zero `NotImplementedError` on v1 code paths
- [ ] `pytest` green locally and in CI (3.9–3.12)
- [ ] `ruff` clean

**CLI**
- [ ] `guardian init --key <key>`
- [ ] `guardian validate policies/minimal.yaml`
- [ ] `guardian status`
- [ ] `guardian logs --tail 10`

**Integration**
- [ ] `examples/quickstart.py` passes with mock + real key
- [ ] Clean venv: `pip install guardian-runtime==1.0.0`

**Release**
- [ ] `CHANGELOG.md` updated
- [ ] Git tag `v1.0.0` + GitHub Release
- [ ] PyPI long description matches README

**Launch**
- [ ] Demo video or GIF in README
- [ ] Show HN / social posts
- [ ] v1.1 milestone issues opened (LangChain, hallucination, portal)

---

## 13. July launch plan — v1.1.0 (Jul 31, 2026)

**Prerequisite:** v1.0.0 shipped and stable on PyPI with ≥3 real users giving feedback.

**One sentence:** Expand from “OpenAI guard wrapper” to **multi-framework, multi-provider, cost-aware** governance — still local-first.

### 13.1 July goals (outcomes)

| # | Goal | Why |
|---|------|-----|
| J1 | **LangChain / framework hook** | Most production AI apps use a framework; meet devs where they are |
| J2 | **Second LLM provider (Anthropic or LiteLLM router)** | Global teams don’t all use OpenAI; one adapter pattern for the rest |
| J3 | **Budget enforcement** | FinOps becomes actionable — stop runaway bills, not just report them |
| J4 | **Optional hallucination check** | Regulated outputs (legal, medical, finance) need grounding checks |
| J5 | **Smarter token controls** | Beyond count + cap — trim old messages, warn on expensive prompts |
| J6 | **5+ active users, bug-driven polish** | July is adoption + feedback, not new architecture docs |

### 13.2 Features to implement in July

| Feature | What it does | Why in July (not June) |
|---------|--------------|------------------------|
| **LangChain callback** | Drop-in handler for LangChain chains/agents | Needs stable `GuardianEngine` from v1 |
| **LiteLLM or provider adapter** | Anthropic / Azure OpenAI / Ollama via same `complete()` API | Abstract only after OpenAI path is proven |
| **Budget manager** | Per-agent daily/monthly spend limits in policy | Builds on v1 token count + local storage |
| **Hard budget block** | Reject LLM call when over limit | Prevents $500 agent-loop incidents |
| **Model downgrade** | Auto-switch to cheaper model at 80% budget | Unique FinOps wedge vs pure observability |
| **Hallucination detector (optional)** | LLM-as-judge vs provided context; policy flag | Extra API call; opt-in only |
| **Context trimmer** | Drop oldest messages when over token budget | Real token *optimization* — harder than count |
| **Presidio optional extra** | NER-based PII via `pip install guardian-runtime[presidio]` | Improves recall; regex sufficient for v1 |
| **Agent loop detection** | Flag repeated identical LLM calls in one session | FinOps + agentic safety |
| **More policies + examples** | `langchain_rag.py`, `cost_tracking.py` | Docs for expanded use cases |

### 13.3 July week-by-week (sketch)

| Week | Dates | Focus |
|------|-------|-------|
| **Week 1** | Jul 1–7 | v1.0 feedback fixes; LangChain callback MVP |
| **Week 2** | Jul 8–14 | Provider adapter (Anthropic or LiteLLM); budget manager |
| **Week 3** | Jul 15–21 | Hard budget block + model downgrade; hallucination opt-in |
| **Week 4** | Jul 22–31 | Context trimmer; Presidio extra; PyPI **1.1.0**; blog post |

### 13.4 Not in July (August+)

| Deferred | When |
|----------|------|
| Developer portal + license API | Aug ([PLAN.md](./PLAN.md) Phase 3) |
| Razorpay / paid tiers | Aug |
| Tool governor | v1.2+ |
| ProductHunt main launch | Sep |

### 13.5 July success criteria

| Metric | Target |
|--------|--------|
| PyPI `1.1.0` published | Jul 31 |
| LangChain integration documented | Yes |
| ≥2 LLM providers | Yes |
| Budget hard-stop works in policy | Yes |
| Active users | ≥5 |
| GitHub issues from v1 users resolved | ≥80% P1 |

---

## 14. Long-term roadmap snapshot

| Version | When | Focus |
|---------|------|-------|
| **0.1.1** | ✅ Jun 1 | PyPI, scanners, policy schema |
| **1.0.0** | Jun 30 | Runtime engine, guards, CLI, logs, OpenAI |
| **1.1.0** | Jul 31 | LangChain, multi-provider, budgets, hallucination |
| **2.0.0** | Sep 2026 | Portal, license API, Razorpay, ProductHunt — [PLAN.md](./PLAN.md) |

---

## 15. Related docs

- [README.md](./README.md) — public install & quickstart
- [CHANGELOG.md](./CHANGELOG.md) — release history
- [PLAN.md](./PLAN.md) — 16-week product & monetization plan
- [ARCHITECTURE.md](./ARCHITECTURE.md) — full technical specification
- [concept.md](./concept.md) — positioning & expert Q&A

---

*Last updated: June 2026 — align this doc when 1.0.0 ships.*
