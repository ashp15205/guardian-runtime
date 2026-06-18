# Changelog

All notable changes to [guardian-runtime](https://pypi.org/project/guardian-runtime/) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.2.0] - 2026-06-18

### Added

- **Native Gemini API Endpoints** — Guardian now speaks the native Google Gemini API format. Two new inbound routes added to the proxy:
  - `POST /v1beta/models/{model}:generateContent` — used by the Gemini CLI and Google GenAI SDK
  - `POST /v1beta/models/{model}:streamGenerateContent` — native SSE streaming for Gemini tools
  - Native `contents`, `parts`, `inlineData`, and `systemInstruction` parsing
  - Gemini-formatted block responses (`candidates` array structure)

- **In-Chat Interactive Override (y/n)** — Guardian no longer just hard-blocks. When a secret or sensitive content is detected, it responds directly inside the AI chat window as the assistant:
  - Shows the violation type, exact detail, and the line number where the threat was found
  - Prompts: *"If you want to proceed anyway, type 'y/n' in your next message."*
  - Works across all three API formats (OpenAI, Anthropic, Gemini) with zero extra config
  - If user types `y/yes` → scanner is bypassed for that request only
  - If user types `n/no` → scanner re-runs and block holds

- **Line Number Detection** — The security scanner now tracks precisely which line in the submitted text or file triggered a violation. The line number is shown directly in the block message so developers can immediately find the exact offending line.

- **File-Type-Aware Interception Router (`file_interceptor.py`)** — Guardian now intercepts base64-encoded file attachments inside JSON payloads and routes them intelligently:
  - Code files (`.py`, `.js`, `.ts`, `.env`, `.yaml`, `.json`, `.sh`, etc.) → Secret Scanner → block if threat found
  - Document files (`.pdf`, `.docx`, `.html`, `.xlsx`, `.txt`) → MarkItDown converter → Markdown injected back into message
  - Conversion failure returns a clear `GuardianRuntimeBlockedError` with the reason

- **`/stats` endpoint** — `GET http://localhost:8080/stats` returns today's session summary: total cost, token usage, blocked count, and document conversions

- **`guardian_runtime convert` CLI** — Manual Markdown export command:
  ```bash
  guardian_runtime convert <file.pdf> --out <file.md>
  ```

### Fixed

- **4 Streaming Bugs Fixed** — Critical logic errors in the SSE streaming handlers for all three API formats:
  - OpenAI stream: `continue` after sending `[GUARDIAN BLOCKED]` caused an infinite loop — changed to `break`
  - Anthropic stream: block text was being yielded as a normal `content_block_delta` *before* checking if it was a block — check moved before yield
  - Anthropic stream: `continue` after block close events kept loop alive — changed to `break`
  - Gemini stream: `continue` after `[GUARDIAN BLOCKED]` marker skipped the final `GuardianRuntimeResponse`, so storage events and violation records were silently dropped — changed to `break`

- **`messages_to_text` now handles nested list content** — `token_counter.py` was extracting text only from string-typed `content` fields. Fixed to recursively unwrap list-typed parts (Anthropic/Gemini multi-part messages), ensuring the `InputGuard` scanner sees all text in nested payloads.

- **`intercept_result` NoneType guard** — When the override flow bypassed the file interceptor, `intercept_result` was `None`, causing `AttributeError: 'NoneType' object has no attribute 'conversions'` when logging. All four storage record calls now correctly use `intercept_result.conversions > 0 if intercept_result else False`.

- **`GuardCheckResult` import in `engine.py`** — Missing import added.

---

## [1.1.1] - 2026-06-06

### Changed
- **Terse Mode Refinement**: Softened the Terse Mode system prompt to retain brief technical reasoning alongside raw code. This achieves an optimal 40-70% output token reduction without data loss, replacing the overly aggressive 94% reduction from the previous version.
- **Documentation**: Reframed Terse Mode as a Dual-Layer Compression Engine across all documentation and updated benchmark claims to reflect empirical data.

## [1.1.0] - 2026-06-06

### Added
- **Terse Mode (`terse_mode`)**: Introduced an extreme FinOps optimization setting in the InputOptimizer. When enabled, it natively injects a system prompt forcing the LLM to reply in terse shorthand, drastically reducing expensive output tokens while maintaining full technical accuracy.

## [1.0.11] - 2026-06-05

### Added
- **`guardian_runtime clean`**: Added a native command to permanently delete all local tracking data, logs, and policies.
- **Documentation Overhaul**: Completely redesigned `index.html` with gorgeous CSS grid layouts and explicitly added Python SDK use cases, Mermaid Architecture diagrams, and Integrations support.
- **Gemini Alias**: Added `gemini` alias to `pyproject.toml` for simpler installation (`pip install guardian_runtime[gemini]`).

### Fixed
- **Status Bug**: Fixed a bug where `guardian_runtime status` would crash trying to call a deprecated method (`get_usage()`).

## [1.0.10] - 2026-06-05

### Fixed
- **CLI Convert Command**: Fixed an attribute naming mismatch (`token_count` to `markdown_tokens`) that caused `guardian_runtime convert` to fail when outputting the token count.

## [1.0.9] - 2026-06-05

### Fixed
- **Heavy Dependencies**: Moved `openai`, `anthropic`, `google-genai`, and `markitdown` to optional dependencies `[project.optional-dependencies]`. This prevents downloading unnecessary heavy SDKs.
- **Client Compatibility**: Fixed a bug where returning HTTP 400 for blocked requests would crash Aider and Cursor. The proxy now returns HTTP 200 with the block explanation.
- **Error Handling**: Provider wrappers now explicitly raise `ImportError` with clear instructions on which optional package to install (e.g. `pip install guardian-runtime[openai]`).
- **Tests**: Restored and modernized the core unit test suite.

## [1.0.8] - 2026-06-05

### Added
- **Anthropic (Claude) provider** — Big 3 complete: OpenAI + Gemini + Anthropic
- `policies/anthropic.yaml` — Claude defaults (`claude-3-5-haiku-latest`)
- Document converter stream support via temp file

### Changed
- v1 feature set locked — see [V1_LAUNCH_PLAN.md](./V1_LAUNCH_PLAN.md)
- Gemini SDK: `google-generativeai` → **`google-genai`** (Client API)
- Token counter: word-estimate for Gemini/Claude; tiktoken for OpenAI only
- Tests: autouse tiktoken mock — no network in CI

---

## [0.2.0] - 2026-06-02

### Added

- **Input Optimizer module** — automatic prompt compression to reduce LLM token costs
  - Whitespace normalization, system prompt deduplication, empty message removal
  - Conversation history trimming (`max_history_messages`)
  - Proactive guidance warnings for bloated inputs
  - Savings metadata in `GuardianRuntimeResponse.optimization`
- **Document Converter** — Microsoft MarkItDown wrapper for PDF/DOCX/XLSX → Markdown (40-70% token savings)
  - Available via `pip install guardian-runtime[optimizer]` (requires Python 3.10+)
- **Convenience APIs** — `optimize_input()`, `convert_document()` for standalone use
- **OptimizerConfig** in YAML policy schema (`optimizer:` section per agent)
- **Optimizer integration in engine pipeline** — runs before Input Guard for maximum efficiency
- **Example policy** — `policies/optimized.yaml` with optimizer enabled
- **Google Gemini provider** — `provider: gemini` in policy or kwarg
- **GuardianRuntimeEngine.complete()** — full governed LLM pipeline
- **Input/Output Guards** — PII, secrets, jailbreak detection on prompts and responses
- **Jailbreak detector** — 40+ regex patterns (DAN, ignore-instructions, role-play)
- **CLI** — `guardian_runtime init`, `validate`, `status`, `logs`
- **Local JSONL logging** at `~/.guardian_runtime/logs/`
- **Local storage** — `~/.guardian_runtime/config.json`, `usage.json`
- **Offline license tier** — works without server; optional `GUARDIAN_RUNTIME_LICENSE_URL`
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
