"""Input optimizer logic for compressing prompts."""
from __future__ import annotations

import re

from guardian_runtime.core.policy import OptimizerConfig
from guardian_runtime.optimizer.models import OptimizeResult
from guardian_runtime.finops.token_counter import count_messages_tokens
from guardian_runtime.finops.cost_calculator import estimate_cost


class InputOptimizer:
    """Optimizes inputs to reduce token count."""

    def __init__(self, config: OptimizerConfig) -> None:
        self.config = config

    def optimize(self, messages: list[dict], model: str = "gpt-4o") -> OptimizeResult:
        if not messages:
            return OptimizeResult(messages, 0, 0, 0.0)

        original_tokens = count_messages_tokens(messages, model)
        actions = []
        guidance = []

        # Start with a copy
        optimized = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]

        # 1. Remove empty messages
        if self.config.remove_empty_messages:
            before_len = len(optimized)
            optimized = [m for m in optimized if str(m["content"]).strip()]
            if len(optimized) < before_len:
                actions.append("remove_empty_messages")

        # 2. Deduplicate system prompts
        if self.config.deduplicate_system_prompts:
            system_msgs = [m for m in optimized if m["role"] == "system"]
            if len(system_msgs) > 1:
                # Merge them
                merged_content = "\n\n".join(m["content"] for m in system_msgs)
                non_system = [m for m in optimized if m["role"] != "system"]
                optimized = [{"role": "system", "content": merged_content}] + non_system
                actions.append("deduplicate_system_prompts")

        # 3. Whitespace normalization
        if self.config.whitespace_normalization:
            changed = False
            for m in optimized:
                original_text = m["content"]
                # Collapse 3+ newlines to 2
                text = re.sub(r'\n{3,}', '\n\n', original_text)
                # Strip trailing spaces on lines
                text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
                if text != original_text:
                    m["content"] = text
                    changed = True
            if changed:
                actions.append("whitespace_normalization")

        # 4. History trimming
        if self.config.max_history_messages is not None and self.config.max_history_messages > 0:
            system_msgs = [m for m in optimized if m["role"] == "system"]
            other_msgs = [m for m in optimized if m["role"] != "system"]
            if len(other_msgs) > self.config.max_history_messages:
                other_msgs = other_msgs[-self.config.max_history_messages:]
                optimized = system_msgs + other_msgs
                actions.append("history_trim")

        # 5. Terse Mode (Output Token Reduction)
        if self.config.terse_mode:
            terse_prompt = (
                "You are a highly efficient technical assistant. Be concise and direct. "
                "Provide brief, clear reasoning alongside the required code. "
                "Do not use conversational filler, pleasantries, or repetitive summaries. "
                "Maintain 100% technical accuracy while minimizing unnecessary wordiness."
            )
            # Find system prompt and append, or insert new one at index 0
            system_msgs = [m for m in optimized if m["role"] == "system"]
            if system_msgs:
                # Modifying the first system message found
                for m in optimized:
                    if m["role"] == "system":
                        m["content"] = f"{m['content']}\n\n{terse_prompt}"
                        break
            else:
                optimized.insert(0, {"role": "system", "content": terse_prompt})
            actions.append("terse_mode_enabled")

        # Calculate results
        optimized_tokens = count_messages_tokens(optimized, model)
        savings_pct = 0.0
        if original_tokens > 0:
            savings_pct = (original_tokens - optimized_tokens) / original_tokens

        # Proactive Guidance
        if original_tokens > 4000:
            guidance.append(f"Input is large ({original_tokens} tokens). "
                            "Consider converting raw documents to markdown using "
                            "`convert_document()` to save up to 70% of tokens.")
        if not self.config.max_history_messages and len(messages) > 10:
            guidance.append("Conversation is getting long. Enable `optimizer.max_history_messages` in your policy to automatically trim older context.")

        cost_saved = 0.0
        if original_tokens > optimized_tokens:
            diff = original_tokens - optimized_tokens
            cost_saved = estimate_cost(input_tokens=diff, output_tokens=0, model=model)

        return OptimizeResult(
            optimized_messages=optimized,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            savings_pct=savings_pct,
            actions_taken=actions,
            estimated_cost_saved=cost_saved,
            guidance=guidance,
        )
