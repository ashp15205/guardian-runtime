# Changelog

All notable changes to [guardian-runtime](https://pypi.org/project/guardian-runtime/) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] — targeting 1.0.0 (2026-06-30)

### Added

- `GuardianEngine.complete()` — governed OpenAI pipeline
- Input/Output guards (PII, secrets, jailbreak)
- CLI: `init`, `validate`, `status`, `logs`
- Local JSONL logging at `~/.guardian/logs/`
- `~/.guardian/` storage and offline license tier
- Token count, cost estimate, optional `max_input_tokens` policy cap
- OpenAI + Gemini providers (`policies/gemini.yaml`)
- `examples/quickstart.py`, `policies/production.yaml`
- GitHub Actions CI
- 92+ tests including integration tests (mocked OpenAI)

See [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md) for the full June sprint.

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
