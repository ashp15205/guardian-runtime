# Guardian Runtime — v1.0 Launch Plan

**Target launch:** June 30, 2026  
**Repo version:** `1.0.0` (code complete)  
**PyPI today:** [0.1.1](https://pypi.org/project/guardian-runtime/) → publish **1.0.0** at launch

---

## 1. Executive summary

Guardian Runtime is a **local-first SDK** between your app and any LLM:

```
User Input → [Input Optimizer] → [Input Guard] → LLM → [Output Guard] → User
                  ↓                    ↓                      ↓
            Token savings         Blocks PII/secrets      Blocks output PII
                                  + jailbreaks
```

**Status: v1 CODE COMPLETE.** All features below are implemented and tested.  
**Remaining:** live provider testing → PyPI 1.0.0 → demo → launch.

---

## 2. v1.0 feature list (locked)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 1 | **PII detection** | ✅ | Aadhaar, PAN, UPI, SSN, credit card, email, phone, passport |
| 2 | **Secret detection** | ✅ | OpenAI, Anthropic, AWS, GitHub, Stripe, Razorpay, Groq, env patterns |
| 3 | **Jailbreak detection** | ✅ | 40+ regex patterns |
| 4 | **Input Optimizer** | ✅ | Whitespace, dedupe system, trim history, empty-msg removal |
| 5 | **Document converter** | ✅ | PDF/DOCX/XLSX → markdown via MarkItDown (`[optimizer]` extra) |
| 6 | **Output guard** | ✅ | PII + secrets on LLM responses |
| 7 | **Policy engine** | ✅ | YAML per agent — guards, optimizer, cost, LLM provider |
| 8 | **OpenAI provider** | ✅ | `OPENAI_API_KEY` |
| 9 | **Gemini provider** | ✅ | `GEMINI_API_KEY` — free tier for testing |
| 10 | **Anthropic provider** | ✅ | `ANTHROPIC_API_KEY` — Big 3 complete |
| 11 | **Local JSONL logs** | ✅ | `~/.guardian/logs/` |
| 12 | **CLI** | ✅ | `init`, `validate`, `status`, `logs` |
| 13 | **Cost tracking** | ✅ | Token count + USD estimate + optional `max_input_tokens` |
| 14 | **Tests + CI** | ✅ | 109 tests, GitHub Actions |

### Not in v1 (v1.1+)

Hallucination judge · LangChain callback · budget hard-stop · portal/billing · Azure/Ollama

---

## 3. Current status

### 3.1 Policies

| File | Provider | Use case |
|------|----------|----------|
| `policies/minimal.yaml` | OpenAI | Default / production OpenAI |
| `policies/gemini.yaml` | Gemini | **Free testing** |
| `policies/anthropic.yaml` | Claude | Anthropic / Big 3 |
| `policies/optimized.yaml` | OpenAI | Full optimizer enabled |
| `policies/production.yaml` | OpenAI | Production defaults |

### 3.2 Quick test

```bash
export GEMINI_API_KEY=your_key          # free — aistudio.google.com
# export ANTHROPIC_API_KEY=...          # console.anthropic.com
# export OPENAI_API_KEY=sk-...

python examples/quickstart.py
guardian validate policies/gemini.yaml
pytest tests/ -q
```

### 3.3 Repository layout

```
guardian/
├── core/           engine, policy, storage, license, models
├── guards/         input_guard, output_guard, validators/
├── optimizer/      input_optimizer, document_converter
├── providers/      openai, gemini, anthropic   ← Big 3
├── finops/         token_counter, cost_calculator
├── logging/        local JSONL
└── cli/            init, validate, status, logs
```

---

## 4. Next steps (release — not coding)

| Step | Action | Owner |
|------|--------|-------|
| 1 | Live test with **Gemini** (free) | You |
| 2 | Live test block: Aadhaar + jailbreak + secret | You |
| 3 | Optional: test Anthropic if you have key | You |
| 4 | Bump + publish **PyPI 1.0.0** | You |
| 5 | Git tag `v1.0.0` + GitHub Release | You |
| 6 | 2-min demo GIF/video in README | You |
| 7 | 3 beta users | You |
| 8 | Show HN / dev Twitter | You |

### Launch checklist

- [x] All v1 features implemented
- [x] Big 3 providers (OpenAI, Gemini, Anthropic)
- [x] 110+ tests green
- [ ] Live Gemini test on your machine
- [ ] PyPI `1.0.0` published
- [ ] Demo video
- [ ] Public launch posts

---

## 5. July v1.1 preview

LangChain callback · budget hard-stop · hallucination (optional) · Azure/Ollama via LiteLLM · context trimmer v2

Portal + Razorpay → August ([PLAN.md](./PLAN.md))

---

## 6. Related docs

- [README.md](./README.md) · [CHANGELOG.md](./CHANGELOG.md) · [PLAN.md](./PLAN.md) · [ARCHITECTURE.md](./ARCHITECTURE.md)

*Last updated: June 2026 — v1 code complete, release pending.*
