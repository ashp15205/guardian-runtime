"""
GuardianRuntime Local Proxy Server
============================
Exposes two API-compatible endpoints:
  POST /v1/chat/completions   — OpenAI format (Aider, Cursor, Copilot CLI)
  POST /v1/messages           — Anthropic format (Claude Code)
  GET  /health                — Health check

Every request is intercepted, scanned by GuardianRuntimeEngine, and forwarded to
the real LLM only if it passes policy. Blocked requests return a valid
response containing a [GUARDIAN_RUNTIME BLOCKED] message so the agent keeps running
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
from starlette.concurrency import run_in_threadpool

from guardian_runtime.core.policy import load_policy, Policy
from guardian_runtime.core.storage import LocalStorage

# ---------------------------------------------------------------------------
# App factory — called with the loaded policy so tests can inject mocks
# ---------------------------------------------------------------------------

def create_proxy_app(policy_path: str | None = None) -> FastAPI:
    """Return a configured FastAPI application for the proxy."""

    if policy_path is not None:
        policy: Policy = load_policy(policy_path)
    else:
        policy = Policy()

    storage = LocalStorage()


    app = FastAPI(
        title="Guardian Runtime API Proxy",
        description="Local-first interceptor for OpenAI-compatible and Gemini APIs",
        version="1.1.3",
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

    def _get_guardian_runtime() -> "GuardianRuntimeEngine":
        """Build a GuardianRuntimeEngine."""
        from guardian_runtime.core.engine import GuardianRuntimeEngine
        return GuardianRuntimeEngine(policy=policy, storage=storage)

    def _identify_tool(request: Request) -> str:
        """Heuristically identify the tool from the User-Agent."""
        user_agent = request.headers.get("user-agent", "").lower()
        if "anthropic" in user_agent:
            return "Claude Code"
        if "openai" in user_agent:
            return "Aider"  # Many CLI tools use openai-python, but Aider is the most common here
        if "cursor" in user_agent:
            return "Cursor"
        if "langchain" in user_agent:
            return "LangChain"
        if user_agent:
            return f"Custom ({user_agent.split('/')[0].capitalize()})"
        return "Unknown Agent"

    def _block_response_openai(violations: list, model: str) -> dict:
        """Format a GuardianRuntime block as a valid OpenAI chat.completion response."""
        types = ", ".join(sorted({v.type for v in violations}))
        details = "; ".join(v.detail for v in violations[:3])
        content = (
            f"[GUARDIAN_RUNTIME BLOCKED] Your request was intercepted by GuardianRuntime Runtime "
            f"and was NOT forwarded to the LLM.\n\n"
            f"Violation type(s): {types}\n"
            f"Detail: {details}\n\n"
            f"Fix the issue and retry. Run `guardian_runtime logs --tail 5` to see the full log entry."
        )
        return {
            "id": f"chatcmpl-guardian_runtime-{uuid.uuid4().hex[:8]}",
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
            "guardian_runtime": {
                "blocked": True,
                "violations": [
                    {"type": v.type, "severity": v.severity, "detail": v.detail}
                    for v in violations
                ],
            },
        }

    def _block_response_anthropic(violations: list, model: str) -> dict:
        """Format a GuardianRuntime block as a valid Anthropic messages response."""
        types = ", ".join(sorted({v.type for v in violations}))
        details = "; ".join(v.detail for v in violations[:3])
        content = (
            f"[GUARDIAN_RUNTIME BLOCKED] Your request was intercepted by GuardianRuntime Runtime "
            f"and was NOT forwarded to the LLM.\n\n"
            f"Violation type(s): {types}\n"
            f"Detail: {details}\n\n"
            f"Fix the issue and retry. Run `guardian_runtime logs --tail 5` to see the full log entry."
        )
        return {
            "id": f"msg_guardian_runtime_{uuid.uuid4().hex[:8]}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "guardian_runtime": {
                "blocked": True,
                "violations": [
                    {"type": v.type, "severity": v.severity, "detail": v.detail}
                    for v in violations
                ],
            },
        }

    def _provider_down_response_openai(error_msg: str, model: str) -> dict:
        content = f"[GUARDIAN_RUNTIME ERROR] {error_msg}"
        return {
            "id": f"chatcmpl-guardian_runtime-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    def _provider_down_response_anthropic(error_msg: str, model: str) -> dict:
        content = f"[GUARDIAN_RUNTIME ERROR] {error_msg}"
        return {
            "id": f"msg_guardian_runtime_{uuid.uuid4().hex[:8]}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    def _success_openai(guardian_runtime_response, model: str) -> dict:
        """Format a GuardianRuntimeResponse as a valid OpenAI chat.completion."""
        return {
            "id": f"chatcmpl-guardian_runtime-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": guardian_runtime_response.model or model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": guardian_runtime_response.content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": guardian_runtime_response.input_tokens,
                "completion_tokens": guardian_runtime_response.output_tokens,
                "total_tokens": guardian_runtime_response.input_tokens + guardian_runtime_response.output_tokens,
            },
        }

    def _success_anthropic(guardian_runtime_response, model: str) -> dict:
        """Format a GuardianRuntimeResponse as a valid Anthropic messages response."""
        return {
            "id": f"msg_guardian_runtime_{uuid.uuid4().hex[:8]}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": guardian_runtime_response.content}],
            "model": guardian_runtime_response.model or model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": guardian_runtime_response.input_tokens,
                "output_tokens": guardian_runtime_response.output_tokens,
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
            "version": "1.1.3",
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

        engine = _get_guardian_runtime()
        
        tool = _identify_tool(request)
        
        if stream:
            async def _sse():
                import json as _json
                import uuid, time
                from starlette.concurrency import run_in_threadpool
                from guardian_runtime.core.models import GuardianRuntimeResponse

                sync_gen = engine.stream(
                    model=model,
                    messages=messages,
                    provider="openai",
                    raise_on_block=False,
                )
                
                base_id = f"chatcmpl-guardian_runtime-{uuid.uuid4().hex[:8]}"
                created = int(time.time())

                while True:
                    try:
                        chunk_or_result = await run_in_threadpool(next, sync_gen)
                    except StopIteration:
                        break
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        yield f"data: {_json.dumps({'error': str(e)})}\n\n"
                        break

                    if isinstance(chunk_or_result, GuardianRuntimeResponse):
                        result = chunk_or_result
                        block_reason = result.violations[0].type if result.blocked and result.violations else None
                        storage.record_request(
                            tool=tool,
                            cost_usd=result.estimated_cost_usd or 0.0,
                            tokens=(result.input_tokens or 0) + (result.output_tokens or 0),
                            blocked=result.blocked,
                            block_reason=block_reason
                        )
                        
                        if not result.blocked:
                            chunk_dict = {
                                "id": base_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                            }
                            yield f"data: {_json.dumps(chunk_dict)}\n\n"
                            yield "data: [DONE]\n\n"
                        break

                    text = chunk_or_result
                    if text.startswith("[GUARDIAN BLOCKED]"):
                        chunk_dict = {
                            "id": base_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                        }
                        yield f"data: {_json.dumps(chunk_dict)}\n\n"
                        yield "data: [DONE]\n\n"
                        continue

                    chunk_dict = {
                        "id": base_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}],
                    }
                    yield f"data: {_json.dumps(chunk_dict)}\n\n"

            return StreamingResponse(
                _sse(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        try:
            result = await run_in_threadpool(
                engine.complete,
                model=model,
                messages=messages,
                provider="openai",
                raise_on_block=False,
            )
            is_error = False
        except Exception as e:
            import traceback
            traceback.print_exc()
            response_body = _provider_down_response_openai(str(e), model)
            result = None
            is_error = True
            
        if not is_error and result:
            block_reason = result.violations[0].type if result.blocked and result.violations else None
            storage.record_request(
                tool=tool,
                cost_usd=result.estimated_cost_usd or 0.0,
                tokens=(result.input_tokens or 0) + (result.output_tokens or 0),
                blocked=result.blocked,
                block_reason=block_reason
            )

            if result.blocked:
                response_body = _block_response_openai(result.violations, model)
            else:
                response_body = _success_openai(result, model)

        return JSONResponse(content=response_body, status_code=500 if is_error else 200)

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

        engine = _get_guardian_runtime()
        
        tool = _identify_tool(request)
        
        if stream:
            async def _sse():
                import json as _json
                import uuid
                from starlette.concurrency import run_in_threadpool
                from guardian_runtime.core.models import GuardianRuntimeResponse

                sync_gen = engine.stream(
                    model=model,
                    messages=messages,
                    provider="anthropic",
                    raise_on_block=False,
                )
                
                msg_id = f"msg_guardian_runtime-{uuid.uuid4().hex[:8]}"

                start_event = {
                    "type": "message_start",
                    "message": {
                        "id": msg_id,
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": model,
                        "stop_reason": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0},
                    },
                }
                yield f"event: message_start\ndata: {_json.dumps(start_event)}\n\n"
                
                block_start = {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}
                yield f"event: content_block_start\ndata: {_json.dumps(block_start)}\n\n"

                while True:
                    try:
                        chunk_or_result = await run_in_threadpool(next, sync_gen)
                    except StopIteration:
                        break
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        yield f"event: error\ndata: {_json.dumps({'error': {'type': 'api_error', 'message': str(e)}})}\n\n"
                        break

                    if isinstance(chunk_or_result, GuardianRuntimeResponse):
                        result = chunk_or_result
                        block_reason = result.violations[0].type if result.blocked and result.violations else None
                        storage.record_request(
                            tool=tool,
                            cost_usd=result.estimated_cost_usd or 0.0,
                            tokens=(result.input_tokens or 0) + (result.output_tokens or 0),
                            blocked=result.blocked,
                            block_reason=block_reason
                        )
                        
                        if not result.blocked:
                            block_stop = {"type": "content_block_stop", "index": 0}
                            yield f"event: content_block_stop\ndata: {_json.dumps(block_stop)}\n\n"
                            msg_delta = {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}}
                            yield f"event: message_delta\ndata: {_json.dumps(msg_delta)}\n\n"
                            yield f"event: message_stop\ndata: {_json.dumps({'type': 'message_stop'})}\n\n"
                        break

                    text = chunk_or_result
                    delta = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}
                    yield f"event: content_block_delta\ndata: {_json.dumps(delta)}\n\n"
                    
                    if text.startswith("[GUARDIAN BLOCKED]"):
                        # Finish up early
                        block_stop = {"type": "content_block_stop", "index": 0}
                        yield f"event: content_block_stop\ndata: {_json.dumps(block_stop)}\n\n"
                        msg_delta = {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}}
                        yield f"event: message_delta\ndata: {_json.dumps(msg_delta)}\n\n"
                        yield f"event: message_stop\ndata: {_json.dumps({'type': 'message_stop'})}\n\n"
                        continue

            return StreamingResponse(
                _sse(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        try:
            result = await run_in_threadpool(
                engine.complete,
                model=model,
                messages=messages,
                provider="anthropic",
                raise_on_block=False,
            )
            is_error = False
        except Exception as e:
            import traceback
            traceback.print_exc()
            response_body = _provider_down_response_anthropic(str(e), model)
            result = None
            is_error = True
            
        if not is_error and result:
            block_reason = result.violations[0].type if result.blocked and result.violations else None
            storage.record_request(
                tool=tool,
                cost_usd=result.estimated_cost_usd or 0.0,
                tokens=(result.input_tokens or 0) + (result.output_tokens or 0),
                blocked=result.blocked,
                block_reason=block_reason
            )

            if result.blocked:
                response_body = _block_response_anthropic(result.violations, model)
            else:
                response_body = _success_anthropic(result, model)

        return JSONResponse(content=response_body, status_code=500 if is_error else 200)

    return app

# Expose a default app instance so uvicorn can run it with workers=4 via import string
# e.g., uvicorn.run("guardian_runtime.proxy.server:app", workers=4)
# The CLI sets GUARDIAN_RUNTIME_POLICY_PATH before invoking uvicorn.
_policy_env = os.environ.get("GUARDIAN_RUNTIME_POLICY_PATH")
app = create_proxy_app(_policy_env)
