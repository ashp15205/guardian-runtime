"""
Guardian Local Proxy Server
============================
Exposes two API-compatible endpoints:
  POST /v1/chat/completions   — OpenAI format (Aider, Cursor, Copilot CLI)
  POST /v1/messages           — Anthropic format (Claude Code)
  GET  /health                — Health check

Every request is intercepted, scanned by GuardianEngine, and forwarded to
the real LLM only if it passes policy. Blocked requests return a valid
response containing a [GUARDIAN BLOCKED] message so the agent keeps running
and the developer sees exactly what was caught.

API keys are read from environment variables:
  OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from guardian.core.policy import load_policy, Policy

# ---------------------------------------------------------------------------
# App factory — called with the loaded policy so tests can inject mocks
# ---------------------------------------------------------------------------

def create_proxy_app(policy_path: str) -> FastAPI:
    """Return a configured FastAPI application for the proxy."""

    policy: Policy = load_policy(policy_path)
    guardian = Guardian(engine=None)  # lazy — we build per-request to pick provider

    app = FastAPI(
        title="Guardian Runtime Proxy",
        description="Local AI firewall proxy for Claude Code, Aider, Cursor, and more.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_guardian(provider: str) -> "GuardianEngine":
        """Build a GuardianEngine for the given provider."""
        from guardian.core.engine import GuardianEngine
        return GuardianEngine(policy=policy)

    def _block_response_openai(violations: list, model: str) -> dict:
        """Format a Guardian block as a valid OpenAI chat.completion response."""
        types = ", ".join(sorted({v.type for v in violations}))
        details = "; ".join(v.detail for v in violations[:3])
        content = (
            f"[GUARDIAN BLOCKED] Your request was intercepted by Guardian Runtime "
            f"and was NOT forwarded to the LLM.\n\n"
            f"Violation type(s): {types}\n"
            f"Detail: {details}\n\n"
            f"Fix the issue and retry. Run `guardian logs --tail 5` to see the full log entry."
        )
        return {
            "id": f"chatcmpl-guardian-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "guardian": {
                "blocked": True,
                "violations": [
                    {"type": v.type, "severity": v.severity, "detail": v.detail}
                    for v in violations
                ],
            },
        }

    def _block_response_anthropic(violations: list, model: str) -> dict:
        """Format a Guardian block as a valid Anthropic messages response."""
        types = ", ".join(sorted({v.type for v in violations}))
        details = "; ".join(v.detail for v in violations[:3])
        content = (
            f"[GUARDIAN BLOCKED] Your request was intercepted by Guardian Runtime "
            f"and was NOT forwarded to the LLM.\n\n"
            f"Violation type(s): {types}\n"
            f"Detail: {details}\n\n"
            f"Fix the issue and retry. Run `guardian logs --tail 5` to see the full log entry."
        )
        return {
            "id": f"msg_guardian_{uuid.uuid4().hex[:8]}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "guardian": {
                "blocked": True,
                "violations": [
                    {"type": v.type, "severity": v.severity, "detail": v.detail}
                    for v in violations
                ],
            },
        }

    def _success_openai(guardian_response, model: str) -> dict:
        """Format a GuardianResponse as a valid OpenAI chat.completion."""
        return {
            "id": f"chatcmpl-guardian-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": guardian_response.model or model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": guardian_response.content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": guardian_response.input_tokens,
                "completion_tokens": guardian_response.output_tokens,
                "total_tokens": guardian_response.input_tokens + guardian_response.output_tokens,
            },
        }

    def _success_anthropic(guardian_response, model: str) -> dict:
        """Format a GuardianResponse as a valid Anthropic messages response."""
        return {
            "id": f"msg_guardian_{uuid.uuid4().hex[:8]}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": guardian_response.content}],
            "model": guardian_response.model or model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": guardian_response.input_tokens,
                "output_tokens": guardian_response.output_tokens,
            },
        }

    # ------------------------------------------------------------------
    # GET /health
    # ------------------------------------------------------------------

    @app.get("/health")
    async def health():
        """Health check — verify the proxy is running."""
        return {
            "status": "ok",
            "version": "1.0.0",
            "policy": policy_path,
            "agents": list(policy.agents.keys()),
        }

    # ------------------------------------------------------------------
    # POST /v1/chat/completions  (OpenAI-compatible)
    # Used by: Aider, Cursor, GitHub Copilot CLI, LiteLLM, OpenAI SDK
    # ------------------------------------------------------------------

    @app.post("/v1/chat/completions")
    async def openai_chat_completions(request: Request):
        body: dict[str, Any] = await request.json()
        messages: list = body.get("messages", [])
        model: str = body.get("model", "gpt-4o")
        stream: bool = body.get("stream", False)

        engine = _get_guardian("openai")
        result = engine.complete(
            model=model,
            messages=messages,
            provider="openai",
        )

        if result.blocked:
            response_body = _block_response_openai(result.violations, model)
        else:
            response_body = _success_openai(result, model)

        if stream:
            # Emit a single chunk then [DONE] — satisfies streaming clients
            def _sse():
                import json as _json
                content = response_body["choices"][0]["message"]["content"]
                chunk = {
                    "id": response_body["id"],
                    "object": "chat.completion.chunk",
                    "created": response_body["created"],
                    "model": response_body["model"],
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": content},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {_json.dumps(chunk)}\n\n"
                # Final chunk with finish_reason
                chunk["choices"][0]["delta"] = {}
                chunk["choices"][0]["finish_reason"] = "stop"
                yield f"data: {_json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                _sse(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        return JSONResponse(content=response_body)

    # ------------------------------------------------------------------
    # POST /v1/messages  (Anthropic-compatible)
    # Used by: Claude Code (claude CLI)
    # ------------------------------------------------------------------

    @app.post("/v1/messages")
    async def anthropic_messages(request: Request):
        body: dict[str, Any] = await request.json()
        messages: list = body.get("messages", [])
        model: str = body.get("model", "claude-3-5-sonnet-20241022")
        stream: bool = body.get("stream", False)

        # Anthropic puts system prompt as a top-level field
        system = body.get("system")
        if system:
            messages = [{"role": "system", "content": system}] + messages

        engine = _get_guardian("anthropic")
        result = engine.complete(
            model=model,
            messages=messages,
            provider="anthropic",
        )

        if result.blocked:
            response_body = _block_response_anthropic(result.violations, model)
        else:
            response_body = _success_anthropic(result, model)

        if stream:
            def _sse():
                import json as _json
                # Anthropic streaming format
                start_event = {
                    "type": "message_start",
                    "message": {
                        "id": response_body["id"],
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": response_body["model"],
                        "stop_reason": None,
                        "usage": response_body["usage"],
                    },
                }
                yield f"event: message_start\ndata: {_json.dumps(start_event)}\n\n"

                content_text = response_body["content"][0]["text"]
                block_start = {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}
                yield f"event: content_block_start\ndata: {_json.dumps(block_start)}\n\n"

                delta = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": content_text}}
                yield f"event: content_block_delta\ndata: {_json.dumps(delta)}\n\n"

                block_stop = {"type": "content_block_stop", "index": 0}
                yield f"event: content_block_stop\ndata: {_json.dumps(block_stop)}\n\n"

                msg_delta = {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}}
                yield f"event: message_delta\ndata: {_json.dumps(msg_delta)}\n\n"

                yield f"event: message_stop\ndata: {_json.dumps({'type': 'message_stop'})}\n\n"

            return StreamingResponse(
                _sse(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        return JSONResponse(content=response_body)

    return app
