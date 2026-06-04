"""Hallucination detector — LLM-as-judge pattern."""
from __future__ import annotations  # Python 3.9 compatibility
# TODO (Week 5): Implement HallucinationDetector
# See ARCHITECTURE.md §4.4.1
# Note: uses developer's OpenAI API key for the judge call, NOT ours

from dataclasses import dataclass, field


@dataclass
class HallucinationResult:
    verdict: str  # "grounded" | "partially_grounded" | "hallucinated"
    confidence: float
    unsupported_claims: list[str] = field(default_factory=list)
    explanation: str = ""

    @property
    def is_hallucination(self) -> bool:
        return self.verdict == "hallucinated"


class HallucinationDetector:
    """Uses a small LLM (gpt-4o-mini) to verify response grounding in context."""

    def __init__(self, judge_model: str = "gpt-4o-mini", threshold: float = 0.7):
        self.judge_model = judge_model
        self.threshold = threshold

    def check(self, question: str, response: str, context: str) -> HallucinationResult:
        """Judge whether the response is grounded in the provided context."""
        raise NotImplementedError
