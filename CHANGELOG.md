# Changelog

All notable changes to [guardian-runtime](https://pypi.org/project/guardian-runtime/) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-06-30

### Added

- **Anthropic (Claude) provider** — Big 3 complete: OpenAI + Gemini + Anthropic
- `policies/anthropic.yaml` — Claude defaults (`claude-3-5-haiku-latest`)
- Document converter stream support via temp file

### Changed

- v1 feature set locked — see [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md)

---

## [0.2.0] - 2026-06-02

### Added

- **Input Optimizer module** — automatic prompt compression to reduce LLM token costs
  - Whitespace normalization, system prompt deduplication, empty message removal
  - Conversation history trimming (`max_history_messages`)
  - Proactive guidance warnings for bloated inputs
  - Savings metadata in `GuardianResponse.optimization`
- **Document Converter** — Microsoft MarkItDown wrapper for PDF/DOCX/XLSX → Markdown (40-70% token savings)
  - Available via `pip install guardian-runtime[optimizer]` (requires Python 3.10+)
- **Convenience APIs** — `optimize_input()`, `convert_document()` for standalone use
- **OptimizerConfig** in YAML policy schema (`optimizer:` section per agent)
- **Optimizer integration in engine pipeline** — runs before Input Guard for maximum efficiency
- **Example policy** — `policies/optimized.yaml` with optimizer enabled
- **Google Gemini provider** — `provider: gemini` in policy or kwarg
- **GuardianEngine.complete()** — full governed LLM pipeline
- **Input/Output Guards** — PII, secrets, jailbreak detection on prompts and responses
- **Jailbreak detector** — 40+ regex patterns (DAN, ignore-instructions, role-play)
- **CLI** — `guardian init`, `validate`, `status`, `logs`
- **Local JSONL logging** at `~/.guardian/logs/`
- **Local storage** — `~/.guardian/config.json`, `usage.json`
- **Offline license tier** — works without server; optional `GUARDIAN_LICENSE_URL`
- **Token count + cost estimate** — tiktoken-based counting with USD estimates
- **Max input tokens** — optional policy cap to block oversized prompts
- **`examples/quickstart.py`**, `policies/production.yaml`, `policies/gemini.yaml`
- 106 tests including integration tests (mocked LLM providers)

### Fixed

- **LicenseManager latency bug** — sync now fires at most once per 24 hours instead of on every `complete()` call. Eliminates up to 10s of blocking network latency per request.

---

## [0.1.1] - 2026-06-01

### Added

- Published to [PyPI](https://pypi.org/project/guardian-runtime/)
- Convenience APIs: `scan_pii()`, `scan_secrets()`
- Secret/credential detection (OpenAI, AWS, GitHub, Stripe, Razorpay, Groq, generic env patterns)
- YAML policy schema (Pydantic validation)

### Fixed

- Packaging and metadata for PyPI distribution

---

## [0.1.0] - 2026-06-01

### Added

- PII detection: Aadhaar, PAN, UPI, SSN, credit card, email, phone, passport
- Policy engine (`load_policy`, example `policies/minimal.yaml`)
- Unit tests for PII and policy (local only, no network)
