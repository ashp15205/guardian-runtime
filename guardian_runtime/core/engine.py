"""GuardianRuntime core engine — orchestrates the full request/response pipeline."""
from __future__ import annotations

import sys
from typing import Any

from guardian_runtime.core.models import GuardianRuntimeBlockedError, GuardianRuntimeResponse, Violation
from guardian_runtime.core.policy import InteractiveMode, LLMProvider, Policy
from guardian_runtime.core.storage import LocalStorage
from guardian_runtime.finops.cost_calculator import estimate_cost
from guardian_runtime.finops.token_counter import count_messages_tokens, count_tokens, messages_to_text
from guardian_runtime.guards.input_guard import InputGuard
from guardian_runtime.guards.output_guard import OutputGuard
from guardian_runtime.logging.local import LocalLogger
from guardian_runtime.optimizer.input_optimizer import InputOptimizer
from guardian_runtime.providers import default_model, get_provider
from guardian_runtime.providers.base import ChatProvider

DEFAULT_BLOCK_MESSAGE = "Request blocked by GuardianRuntime Runtime policy."


class GuardianRuntimeEngine:
    """Orchestrates: input guard → LLM → output guard → log."""

    def __init__(
        self,
        policy: Policy,
        storage: LocalStorage | None = None,
        logger: LocalLogger | None = None,
        providers: dict[str, ChatProvider] | None = None,
        openai_client: Any | None = None,
    ) -> None:
        self.policy = policy
        self.storage = storage or LocalStorage()
        self.logger = logger or LocalLogger()
        self.input_guard = InputGuard()
        self.output_guard = OutputGuard()
        self._providers: dict[str, ChatProvider] = dict(providers or {})
        if openai_client is not None:
            from guardian_runtime.providers.openai_provider import OpenAIProvider

            self._providers["openai"] = OpenAIProvider(client=openai_client)
        self._session_spend: dict[str, float] = {}

    def complete(
        self,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        agent_id: str = "default",
        session_id: str | None = None,
        provider: str | None = None,
        raise_on_block: bool = True,
        **kwargs: Any,
    ) -> GuardianRuntimeResponse:
        """Full governed LLM call. Returns GuardianRuntimeResponse."""
        if messages is None:
            messages = []

        agent_policy = self.policy.get_agent(agent_id)
        violations: list[Violation] = []

        provider_name = self._resolve_provider_name(agent_policy, provider)
        model_name = model or self._resolve_model(agent_policy, provider_name)

        input_tokens = count_messages_tokens(messages, model_name)
        
        # --- Optimizer Step ---
        optimization_meta = None
        if agent_policy.optimizer and agent_policy.optimizer.enabled:
            optimizer = InputOptimizer(agent_policy.optimizer)
            opt_result = optimizer.optimize(messages, model_name)
            messages = opt_result.optimized_messages
            input_tokens = opt_result.optimized_tokens
            optimization_meta = {
                "original_tokens": opt_result.original_tokens,
                "optimized_tokens": opt_result.optimized_tokens,
                "savings_pct": opt_result.savings_pct,
                "actions_taken": opt_result.actions_taken,
                "estimated_cost_saved": opt_result.estimated_cost_saved,
                "guidance": opt_result.guidance,
            }
            if opt_result.guidance:
                for g in opt_result.guidance:
                    self.logger.log_event("optimizer_guidance", agent_id, session_id, [], {"message": g})
                    
        cost_config = agent_policy.cost
        max_input = cost_config.max_input_tokens if cost_config else None
        daily_budget = cost_config.daily_budget if cost_config else None
        
        # Check token limit
        if max_input is not None and input_tokens > max_input:
            violations.append(
                Violation(
                    type="token_limit",
                    severity="high",
                    detail=f"Input tokens ({input_tokens}) exceed limit ({max_input})",
                    action="blocked",
                    metadata={"input_tokens": input_tokens, "limit": max_input},
                )
            )
            
        # Check daily budget limit
        if daily_budget is not None:
            current_spend = self.storage.get_daily_spend()
            estimated_input_cost = estimate_cost(input_tokens, 0, model_name)
            if current_spend + estimated_input_cost > daily_budget:
                violations.append(
                    Violation(
                        type="budget_exceeded",
                        severity="critical",
                        detail=f"Daily budget of ${daily_budget:.2f} exceeded. Current spend: ${current_spend:.2f}. Update 'daily_budget' in policy.yaml to continue.",
                        action="blocked",
                        metadata={"current_spend": current_spend, "budget": daily_budget},
                    )
                )

        if any(v.action == "blocked" for v in violations):
            response = self._blocked_response(
                violations,
                model_name,
                input_tokens=input_tokens,
                provider=provider_name,
            )
            self._finalize(response, agent_id, session_id)
            if raise_on_block:
                raise GuardianRuntimeBlockedError(response)
            return response

        input_text = messages_to_text(messages)
        input_result = self.input_guard.check(input_text, agent_policy)
        violations.extend(input_result.violations)

        if not input_result.allowed:
            # --- Interactive (warn-and-ask) mode for local development ---
            if self.policy.interactive_mode == InteractiveMode.WARN_ASK:
                if self._interactive_allow(input_result.violations, provider_name):
                    # Developer chose to proceed — treat input as clean
                    input_result = type(input_result)(
                        allowed=True,
                        violations=[],
                        processed_text=input_result.processed_text,
                    )
                    violations = [v for v in violations if v not in input_result.violations]
                else:
                    response = self._blocked_response(
                        violations,
                        model_name,
                        input_tokens=input_tokens,
                        provider=provider_name,
                    )
                    self._finalize(response, agent_id, session_id)
                    if raise_on_block:
                        raise GuardianRuntimeBlockedError(response)
                    return response
            else:
                response = self._blocked_response(
                    violations,
                    model_name,
                    input_tokens=input_tokens,
                    provider=provider_name,
                )
                self._finalize(response, agent_id, session_id)
                if raise_on_block:
                    raise GuardianRuntimeBlockedError(response)
                return response

        llm_messages = messages
        if input_result.processed_text is not None:
            llm_messages = self._apply_redacted_input(messages, input_result.processed_text)

        chat_provider = self._get_provider(provider_name)
        llm_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ("provider", "raise_on_block")
        }
        result = chat_provider.complete(model_name, llm_messages, **llm_kwargs)

        content = result.content
        if result.output_tokens is not None:
            output_tokens = result.output_tokens
        else:
            output_tokens = count_tokens(content, model_name)
        if result.input_tokens is not None:
            input_tokens = result.input_tokens

        output_result = self.output_guard.check(content, agent_policy)
        violations.extend(output_result.violations)

        estimated_cost = estimate_cost(input_tokens, output_tokens, model_name)
        if session_id:
            self._session_spend[session_id] = (
                self._session_spend.get(session_id, 0.0) + estimated_cost
            )

        response = GuardianRuntimeResponse(
            content=content,
            blocked=False,
            violations=[v for v in violations if v.action == "flagged"],
            model=model_name,
            provider=provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost,
            optimization=optimization_meta,
            raw_response=result.raw_response,
        )
        self._finalize(response, agent_id, session_id)
        return response

    def stream(
        self,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        agent_id: str = "default",
        session_id: str | None = None,
        provider: str | None = None,
        raise_on_block: bool = True,
        **kwargs: Any,
    ) -> Any:
        if messages is None:
            messages = []

        agent_policy = self.policy.get_agent(agent_id)
        violations: list[Violation] = []

        provider_name = self._resolve_provider_name(agent_policy, provider)
        model_name = model or self._resolve_model(agent_policy, provider_name)

        input_tokens = count_messages_tokens(messages, model_name)
        
        optimization_meta = None
        if agent_policy.optimizer and agent_policy.optimizer.enabled:
            optimizer = InputOptimizer(agent_policy.optimizer)
            opt_result = optimizer.optimize(messages, model_name)
            messages = opt_result.optimized_messages
            input_tokens = opt_result.optimized_tokens
            optimization_meta = {
                "original_tokens": opt_result.original_tokens,
                "optimized_tokens": opt_result.optimized_tokens,
                "savings_pct": opt_result.savings_pct,
                "actions_taken": opt_result.actions_taken,
                "estimated_cost_saved": opt_result.estimated_cost_saved,
                "guidance": opt_result.guidance,
            }
            if opt_result.guidance:
                for g in opt_result.guidance:
                    self.logger.log_event("optimizer_guidance", agent_id, session_id, [], {"message": g})
                    
        cost_config = agent_policy.cost
        max_input = cost_config.max_input_tokens if cost_config else None
        daily_budget = cost_config.daily_budget if cost_config else None
        
        if max_input is not None and input_tokens > max_input:
            violations.append(
                Violation(
                    type="token_limit",
                    severity="high",
                    detail=f"Input tokens ({input_tokens}) exceed limit ({max_input})",
                    action="blocked",
                    metadata={"input_tokens": input_tokens, "limit": max_input},
                )
            )
            
        if daily_budget is not None:
            current_spend = self.storage.get_daily_spend()
            estimated_input_cost = estimate_cost(input_tokens, 0, model_name)
            if current_spend + estimated_input_cost > daily_budget:
                violations.append(
                    Violation(
                        type="budget_exceeded",
                        severity="critical",
                        detail=f"Daily budget of ${daily_budget:.2f} exceeded. Current spend: ${current_spend:.2f}. Update 'daily_budget' in policy.yaml to continue.",
                        action="blocked",
                        metadata={"current_spend": current_spend, "budget": daily_budget},
                    )
                )

        if any(v.action == "blocked" for v in violations):
            response = self._blocked_response(
                violations,
                model_name,
                input_tokens=input_tokens,
                provider=provider_name,
            )
            self._finalize(response, agent_id, session_id)
            yield f"[GUARDIAN BLOCKED] {violations[0].detail}"
            yield response
            return

        input_text = messages_to_text(messages)
        input_result = self.input_guard.check(input_text, agent_policy)
        violations.extend(input_result.violations)

        if not input_result.allowed:
            # Handle interactive mode
            if self.policy.interactive_mode == InteractiveMode.WARN_ASK:
                if self._interactive_allow(input_result.violations, provider_name):
                    input_result = type(input_result)(
                        allowed=True,
                        violations=[],
                        processed_text=input_result.processed_text,
                    )
                    violations = [v for v in violations if v not in input_result.violations]
                else:
                    response = self._blocked_response(
                        violations,
                        model_name,
                        input_tokens=input_tokens,
                        provider=provider_name,
                    )
                    self._finalize(response, agent_id, session_id)
                    yield f"[GUARDIAN BLOCKED] {violations[0].detail}"
                    yield response
                    return
            else:
                response = self._blocked_response(
                    violations,
                    model_name,
                    input_tokens=input_tokens,
                    provider=provider_name,
                )
                self._finalize(response, agent_id, session_id)
                yield f"[GUARDIAN BLOCKED] {violations[0].detail}"
                yield response
                return

        llm_messages = messages
        if input_result.processed_text is not None:
            llm_messages = self._apply_redacted_input(messages, input_result.processed_text)

        chat_provider = self._get_provider(provider_name)
        llm_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ("provider", "raise_on_block")
        }
        
        stream_generator = chat_provider.stream(model_name, llm_messages, **llm_kwargs)
        
        result = None
        try:
            while True:
                chunk = next(stream_generator)
                yield chunk
        except StopIteration as e:
            result = e.value
            
        if not result:
            return

        content = result.content
        if result.output_tokens is not None:
            output_tokens = result.output_tokens
        else:
            output_tokens = count_tokens(content, model_name)
        if result.input_tokens is not None:
            input_tokens = result.input_tokens

        output_result = self.output_guard.check(content, agent_policy)
        violations.extend(output_result.violations)

        estimated_cost = estimate_cost(input_tokens, output_tokens, model_name)
        if session_id:
            self._session_spend[session_id] = (
                self._session_spend.get(session_id, 0.0) + estimated_cost
            )

        response = GuardianRuntimeResponse(
            content=content,
            blocked=False,
            violations=[v for v in violations if v.action == "flagged"],
            model=model_name,
            provider=provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost,
            optimization=optimization_meta,
            raw_response=result.raw_response,
        )
        self._finalize(response, agent_id, session_id)
        yield response

    def get_cost_report(self, agent_id: str) -> dict:
        """Return local cost report for the given agent."""
        total = sum(self._session_spend.values())
        return {
            "agent_id": agent_id,
            "sessions": len(self._session_spend),
            "total_estimated_cost_usd": round(total, 6),
            "session_spend": dict(self._session_spend),
        }

    def _get_provider(self, name: str) -> ChatProvider:
        key = name.lower()
        if key in self._providers:
            return self._providers[key]
        provider = get_provider(key)
        self._providers[key] = provider
        return provider

    @staticmethod
    def _resolve_provider_name(agent_policy, override: str | None) -> str:
        if override:
            return override.lower()
        if agent_policy.llm is not None:
            return agent_policy.llm.provider.value
        return LLMProvider.OPENAI.value

    @staticmethod
    def _resolve_model(agent_policy, provider_name: str) -> str:
        if agent_policy.llm is not None and agent_policy.llm.default_model:
            return agent_policy.llm.default_model
        return default_model(provider_name)

    def _blocked_response(
        self,
        violations: list[Violation],
        model: str | None,
        input_tokens: int = 0,
        provider: str | None = None,
    ) -> GuardianRuntimeResponse:
        return GuardianRuntimeResponse(
            content=DEFAULT_BLOCK_MESSAGE,
            blocked=True,
            violations=violations,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
        )

    def _finalize(
        self,
        response: GuardianRuntimeResponse,
        agent_id: str,
        session_id: str | None,
        count_usage: bool = True,
    ) -> None:
        self.logger.log_response(response, agent_id, session_id)
        if count_usage:
            self.storage.increment_usage()
            if response.estimated_cost_usd is not None and response.estimated_cost_usd > 0:
                self.storage.add_spend(response.estimated_cost_usd)

    @staticmethod
    def _interactive_allow(violations: list[Violation], provider_name: str) -> bool:
        """Print a rich terminal warning and ask the developer whether to proceed.

        Returns True if the developer confirms they want to send the prompt anyway.
        Only called when policy.interactive_mode == 'warn_ask'.
        """
        YELLOW = "\033[33m"
        RED    = "\033[31m"
        BOLD   = "\033[1m"
        RESET  = "\033[0m"
        
        provider_display = provider_name.capitalize() if provider_name else "the LLM"

        print(
            f"\n{BOLD}{RED}🚨  GUARDIAN_RUNTIME SECURITY ALERT{RESET}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}GuardianRuntime detected the following issues in your prompt:{RESET}",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  • [{v.type.upper()}] {v.detail}", file=sys.stderr)

        print(
            f"\n{BOLD}Do you still want to send this prompt to {provider_display}?{RESET}"
            f"  {YELLOW}[y/N]{RESET} ",
            end="",
            file=sys.stderr,
        )
        try:
            answer = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        print("", file=sys.stderr)
        return answer == "y"

    @staticmethod
    def _apply_redacted_input(messages: list[dict[str, Any]], redacted: str) -> list[dict[str, Any]]:
        """Replace the last user message content with redacted text."""
        updated = [dict(m) for m in messages]
        for idx in range(len(updated) - 1, -1, -1):
            if updated[idx].get("role") == "user":
                updated[idx] = {**updated[idx], "content": redacted}
                break
        return updated
