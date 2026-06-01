"""Guardian core engine — orchestrates the full request/response pipeline."""
from __future__ import annotations  # Python 3.9 compatibility
# TODO (Week 6): Implement GuardianEngine.complete() pipeline


class GuardianEngine:
    """Orchestrates: license check → input guard → LLM → output guard → log."""

    def __init__(self, policy):
        self.policy = policy
        # TODO: initialize sub-components from policy

    def complete(self, model, messages, agent_id="default", session_id=None, **kwargs):
        """Full governed LLM call. Returns GuardianResponse."""
        raise NotImplementedError("Engine not yet implemented — see ARCHITECTURE.md §4.2")

    def get_cost_report(self, agent_id: str) -> dict:
        """Return local cost report for the given agent."""
        raise NotImplementedError
