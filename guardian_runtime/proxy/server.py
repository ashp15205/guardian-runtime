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
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from starlette.concurrency import run_in_threadpool

from guardian_runtime.core.policy import load_policy, Policy
from guardian_runtime.core.storage import LocalStorage
from guardian_runtime.core.file_interceptor import FileInterceptor

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
    file_interceptor = FileInterceptor()


    app = FastAPI(
        title="Guardian Runtime API Proxy",
        description="Local-first interceptor for OpenAI-compatible and Gemini APIs",
        version="1.1.4",
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
        
        detail_lines = [v.detail for v in violations[:3]]
        details = "; ".join(detail_lines)
        
        content = (
            f"[GUARDIAN_RUNTIME BLOCKED] Your request was intercepted by GuardianRuntime Runtime.\n\n"
            f"Violation type(s): {types}\n"
            f"Detail: {details}\n\n"
            f"If you want to proceed anyway, type 'y/n' in your next message."
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
        
        detail_lines = [v.detail for v in violations[:3]]
        details = "; ".join(detail_lines)
        
        content = (
            f"[GUARDIAN_RUNTIME BLOCKED] Your request was intercepted by GuardianRuntime Runtime.\n\n"
            f"Violation type(s): {types}\n"
            f"Detail: {details}\n\n"
            f"If you want to proceed anyway, type 'y/n' in your next message."
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

    def _parse_gemini_messages(body: dict) -> list:
        messages = []
        sys_inst = body.get("systemInstruction")
        if sys_inst and isinstance(sys_inst, dict):
            parts = sys_inst.get("parts", [])
            text = "".join([p.get("text", "") for p in parts if "text" in p])
            if text:
                messages.append({"role": "system", "content": text})

        for content in body.get("contents", []):
            role = content.get("role", "user")
            # Gemini uses "model", Guardian uses "assistant"
            if role == "model":
                role = "assistant"
                
            parts = []
            for part in content.get("parts", []):
                if "text" in part:
                    parts.append({"type": "text", "text": part["text"]})
                elif "inlineData" in part:
                    parts.append({
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": part["inlineData"].get("mimeType", ""),
                            "data": part["inlineData"].get("data", "")
                        }
                    })
            if parts:
                messages.append({"role": role, "content": parts})
        return messages

    def _block_response_gemini(violations: list) -> dict:
        types = ", ".join(sorted({v.type for v in violations}))
        detail_lines = [v.detail for v in violations[:3]]
        details = "; ".join(detail_lines)
        
        content = (
            f"[GUARDIAN_RUNTIME BLOCKED] Your request was intercepted by GuardianRuntime Runtime.\n\n"
            f"Violation type(s): {types}\n"
            f"Detail: {details}\n\n"
            f"If you want to proceed anyway, type 'y/n' in your next message."
        )
        return {
            "candidates": [
                {
                    "content": {"parts": [{"text": content}], "role": "model"},
                    "finishReason": "STOP",
                    "index": 0
                }
            ],
            "usageMetadata": {"promptTokenCount": 0, "candidatesTokenCount": 0, "totalTokenCount": 0},
            "guardian_runtime": {
                "blocked": True,
                "violations": [{"type": v.type, "severity": v.severity, "detail": v.detail} for v in violations]
            }
        }

    def _success_gemini(guardian_runtime_response) -> dict:
        return {
            "candidates": [
                {
                    "content": {"parts": [{"text": guardian_runtime_response.content}], "role": "model"},
                    "finishReason": "STOP",
                    "index": 0
                }
            ],
            "usageMetadata": {
                "promptTokenCount": guardian_runtime_response.input_tokens or 0,
                "candidatesTokenCount": guardian_runtime_response.output_tokens or 0,
                "totalTokenCount": (guardian_runtime_response.input_tokens or 0) + (guardian_runtime_response.output_tokens or 0)
            }
        }

    def _provider_down_response_gemini(error_msg: str) -> dict:
        content = f"[GUARDIAN_RUNTIME ERROR] {error_msg}"
        return {
            "candidates": [
                {
                    "content": {"parts": [{"text": content}], "role": "model"},
                    "finishReason": "STOP",
                    "index": 0
                }
            ]
        }

    # ------------------------------------------------------------------
    # GET /health
    # ------------------------------------------------------------------

    @app.get("/health")
    async def health():
        """Health check — verify the proxy is running."""
        return {
            "status": "ok",
            "version": "1.1.4",
            "policy": policy_path,
            "agents": list(policy.agents.keys()),
        }

    @app.get("/stats")
    async def stats():
        """Return today's session summary."""
        return storage.get_today_stats()

    @app.get("/dashboard", response_class=HTMLResponse)
    async def get_dashboard():
        """Serve the beautiful analytics dashboard."""
        import pathlib
        html_path = pathlib.Path(__file__).parent / "dashboard.html"
        if not html_path.exists():
            return HTMLResponse("Dashboard HTML not found.", status_code=404)
        return HTMLResponse(html_path.read_text(encoding="utf-8"))

    @app.get("/api/time_series")
    async def get_time_series(days: int = 7):
        """Return time series data for the dashboard chart."""
        return storage.get_time_series(days=days)

    # ------------------------------------------------------------------
    # POST /v1/chat/completions  (OpenAI-compatible)
    # Used by: Aider, Cursor, GitHub Copilot CLI, LiteLLM, OpenAI SDK
    # ------------------------------------------------------------------

    def _is_override(msgs: list) -> bool:
        if len(msgs) < 2:
            return False
            
        last_msg = msgs[-1]
        prev_msg = msgs[-2]
        
        if last_msg.get("role") != "user":
            return False
            
        content = last_msg.get("content", "")
        if isinstance(content, list):
            texts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
            text_str = "\n".join(texts).strip().lower()
        else:
            text_str = str(content).strip().lower()
            
        if text_str not in ["y", "yes", "n", "no"]:
            return False
            
        # If user types "n" or "no", we do not override, we let the scanner block it again or process normally.
        if text_str in ["n", "no"]:
            return False
            
        if prev_msg.get("role") != "assistant":
            return False
            
        prev_content = prev_msg.get("content", "")
        if isinstance(prev_content, list):
            prev_texts = [b.get("text", "") for b in prev_content if isinstance(b, dict) and b.get("type") == "text"]
            prev_text_str = "\n".join(prev_texts)
        else:
            prev_text_str = str(prev_content)
            
        return "[GUARDIAN_RUNTIME BLOCKED]" in prev_text_str

    @app.post("/v1/chat/completions")
    async def openai_chat_completions(request: Request):
        body: dict[str, Any] = await request.json()
        messages: list = body.get("messages", [])
        model: str = body.get("model", "gpt-4o")
        stream: bool = body.get("stream", False)

        tool = _identify_tool(request)
        
        is_override = _is_override(messages)
        if is_override:
            # Strip the block message and the user's override message to resume previous context
            messages = messages[:-2]
            
        intercept_result = None
        if not is_override:
            intercept_result = file_interceptor.process_messages(messages)
            messages = intercept_result.messages
            if intercept_result.violations:
                storage.record_request(
                    tool=tool, cost_usd=0.0, tokens=0, blocked=True, 
                    block_reason=intercept_result.violations[0].type,
                    file_converted=False, 
                    secrets_blocked=len([v for v in intercept_result.violations if v.type == "secret"])
                )
                return JSONResponse(content=_block_response_openai(intercept_result.violations, model), status_code=200)

        engine = _get_guardian_runtime()
        
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
                    skip_input_guard=is_override,
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
                            block_reason=block_reason,
                            file_converted=intercept_result.conversions > 0 if intercept_result else False,
                            secrets_blocked=len([v for v in result.violations if v.type == "secret"])
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
                        break  # Bug fix: was 'continue' — loop must stop after sending block

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
                skip_input_guard=is_override,
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
                block_reason=block_reason,
                file_converted=intercept_result.conversions > 0 if intercept_result else False,
                secrets_blocked=len([v for v in result.violations if v.type == "secret"])
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

        tool = _identify_tool(request)
        
        is_override = _is_override(messages)
        if is_override:
            # Strip the block message and the user's override message
            messages = messages[:-2]
            
        intercept_result = None
        if not is_override:
            intercept_result = file_interceptor.process_messages(messages)
            messages = intercept_result.messages
            if intercept_result.violations:
                storage.record_request(
                    tool=tool, cost_usd=0.0, tokens=0, blocked=True, 
                    block_reason=intercept_result.violations[0].type,
                    file_converted=False, 
                    secrets_blocked=len([v for v in intercept_result.violations if v.type == "secret"])
                )
                return JSONResponse(content=_block_response_anthropic(intercept_result.violations, model), status_code=200)

        engine = _get_guardian_runtime()
        
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
                    skip_input_guard=is_override,
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
                            block_reason=block_reason,
                            file_converted=intercept_result.conversions > 0 if intercept_result else False,
                            secrets_blocked=len([v for v in result.violations if v.type == "secret"])
                        )
                        
                        if not result.blocked:
                            block_stop = {"type": "content_block_stop", "index": 0}
                            yield f"event: content_block_stop\ndata: {_json.dumps(block_stop)}\n\n"
                            msg_delta = {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}}
                            yield f"event: message_delta\ndata: {_json.dumps(msg_delta)}\n\n"
                            yield f"event: message_stop\ndata: {_json.dumps({'type': 'message_stop'})}\n\n"
                        break

                    text = chunk_or_result
                    # Bug fix: check BEFORE yielding so block text doesn't appear as a regular delta
                    if text.startswith("[GUARDIAN BLOCKED]"):
                        delta = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}
                        yield f"event: content_block_delta\ndata: {_json.dumps(delta)}\n\n"
                        block_stop = {"type": "content_block_stop", "index": 0}
                        yield f"event: content_block_stop\ndata: {_json.dumps(block_stop)}\n\n"
                        msg_delta = {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}}
                        yield f"event: message_delta\ndata: {_json.dumps(msg_delta)}\n\n"
                        yield f"event: message_stop\ndata: {_json.dumps({'type': 'message_stop'})}\n\n"
                        break  # Bug fix: was 'continue' — loop must stop after sending block

                    delta = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}
                    yield f"event: content_block_delta\ndata: {_json.dumps(delta)}\n\n"

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
                skip_input_guard=is_override,
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
                block_reason=block_reason,
                file_converted=intercept_result.conversions > 0 if intercept_result else False,
                secrets_blocked=len([v for v in result.violations if v.type == "secret"])
            )

            if result.blocked:
                response_body = _block_response_anthropic(result.violations, model)
            else:
                response_body = _success_anthropic(result, model)

        return JSONResponse(content=response_body, status_code=500 if is_error else 200)

    # ------------------------------------------------------------------
    # POST /v1beta/models/{model}:generateContent (Gemini-compatible)
    # Used by: Native Gemini CLI, Google GenAI SDK
    # ------------------------------------------------------------------

    @app.post("/v1beta/models/{model}:generateContent")
    async def gemini_generate_content(request: Request, model: str):
        body: dict[str, Any] = await request.json()
        messages = _parse_gemini_messages(body)

        tool = _identify_tool(request)
        if "gemini" not in tool.lower() and "google" not in tool.lower():
             tool = "Gemini CLI / SDK"
             
        is_override = _is_override(messages)
        if is_override:
            messages = messages[:-2]
            
        intercept_result = None
        if not is_override:
            intercept_result = file_interceptor.process_messages(messages)
            messages = intercept_result.messages
            if intercept_result.violations:
                storage.record_request(
                    tool=tool, cost_usd=0.0, tokens=0, blocked=True, 
                    block_reason=intercept_result.violations[0].type,
                    file_converted=False, 
                    secrets_blocked=len([v for v in intercept_result.violations if v.type == "secret"])
                )
                return JSONResponse(content=_block_response_gemini(intercept_result.violations), status_code=200)

        engine = _get_guardian_runtime()
        
        try:
            result = await run_in_threadpool(
                engine.complete,
                model=model,
                messages=messages,
                provider="gemini",
                raise_on_block=False,
                skip_input_guard=is_override,
            )
            is_error = False
        except Exception as e:
            import traceback
            traceback.print_exc()
            response_body = _provider_down_response_gemini(str(e))
            result = None
            is_error = True
            
        if not is_error and result:
            block_reason = result.violations[0].type if result.blocked and result.violations else None
            storage.record_request(
                tool=tool,
                cost_usd=result.estimated_cost_usd or 0.0,
                tokens=(result.input_tokens or 0) + (result.output_tokens or 0),
                blocked=result.blocked,
                block_reason=block_reason,
                file_converted=intercept_result.conversions > 0 if intercept_result else False,
                secrets_blocked=len([v for v in result.violations if v.type == "secret"])
            )

            if result.blocked:
                response_body = _block_response_gemini(result.violations)
            else:
                response_body = _success_gemini(result)

        return JSONResponse(content=response_body, status_code=500 if is_error else 200)

    @app.post("/v1beta/models/{model}:streamGenerateContent")
    async def gemini_stream_generate_content(request: Request, model: str):
        body: dict[str, Any] = await request.json()
        messages = _parse_gemini_messages(body)

        tool = _identify_tool(request)
        if "gemini" not in tool.lower() and "google" not in tool.lower():
             tool = "Gemini CLI / SDK"
             
        is_override = _is_override(messages)
        if is_override:
            messages = messages[:-2]
            
        intercept_result = None
        if not is_override:
            intercept_result = file_interceptor.process_messages(messages)
            messages = intercept_result.messages
            if intercept_result.violations:
                storage.record_request(
                    tool=tool, cost_usd=0.0, tokens=0, blocked=True, 
                    block_reason=intercept_result.violations[0].type,
                    file_converted=False, 
                    secrets_blocked=len([v for v in intercept_result.violations if v.type == "secret"])
                )
                return JSONResponse(content=_block_response_gemini(intercept_result.violations), status_code=200)

        engine = _get_guardian_runtime()
        
        async def _sse():
            import json as _json
            from starlette.concurrency import run_in_threadpool
            from guardian_runtime.core.models import GuardianRuntimeResponse

            sync_gen = engine.stream(
                model=model,
                messages=messages,
                provider="gemini",
                raise_on_block=False,
                skip_input_guard=is_override,
            )
            
            while True:
                try:
                    chunk_or_result = await run_in_threadpool(next, sync_gen)
                except StopIteration:
                    break
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    yield f"data: {_json.dumps(_provider_down_response_gemini(str(e)))}\n\n"
                    break

                if isinstance(chunk_or_result, GuardianRuntimeResponse):
                    result = chunk_or_result
                    block_reason = result.violations[0].type if result.blocked and result.violations else None
                    storage.record_request(
                        tool=tool,
                        cost_usd=result.estimated_cost_usd or 0.0,
                        tokens=(result.input_tokens or 0) + (result.output_tokens or 0),
                        blocked=result.blocked,
                        block_reason=block_reason,
                        file_converted=intercept_result.conversions > 0 if intercept_result else False,
                        secrets_blocked=len([v for v in result.violations if v.type == "secret"])
                    )
                    
                    if result.blocked:
                        yield f"data: {_json.dumps(_block_response_gemini(result.violations))}\n\n"
                        
                    break

                text = chunk_or_result
                if text.startswith("[GUARDIAN BLOCKED]"):
                    break  # Bug fix: was 'continue' — loop must stop, GuardianRuntimeResponse follows and has the violations

                chunk_dict = {
                    "candidates": [
                        {
                            "content": {"parts": [{"text": text}], "role": "model"},
                            "finishReason": None,
                            "index": 0
                        }
                    ]
                }
                yield f"data: {_json.dumps(chunk_dict)}\n\n"

        return StreamingResponse(
            _sse(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app

# Expose a default app instance so uvicorn can run it with workers=4 via import string
# e.g., uvicorn.run("guardian_runtime.proxy.server:app", workers=4)
# The CLI sets GUARDIAN_RUNTIME_POLICY_PATH before invoking uvicorn.
_policy_env = os.environ.get("GUARDIAN_RUNTIME_POLICY_PATH")
app = create_proxy_app(_policy_env)
