"""Local JSONL logging for violations and checks."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from guardian.core.models import GuardianResponse, Violation
from guardian.core.storage import GUARDIAN_DIR

LOGS_DIR = GUARDIAN_DIR / "logs"


class LocalLogger:
    """Appends structured events to ~/.guardian/logs/YYYY-MM-DD.jsonl."""

    def __init__(self, logs_dir: Path | None = None) -> None:
        self.logs_dir = logs_dir or LOGS_DIR

    def _log_path(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.logs_dir / f"{day}.jsonl"

    def log_event(
        self,
        event_type: str,
        agent_id: str,
        session_id: str | None,
        violations: list[Violation],
        metadata: dict | None = None,
    ) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "agent_id": agent_id,
            "session_id": session_id,
            "violations": [
                {
                    "type": v.type,
                    "severity": v.severity,
                    "detail": v.detail,
                    "action": v.action,
                    "metadata": v.metadata,
                }
                for v in violations
            ],
            "metadata": metadata or {},
        }
        with open(self._log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_response(
        self,
        response: GuardianResponse,
        agent_id: str,
        session_id: str | None,
    ) -> None:
        event = "blocked" if response.blocked else "allowed"
        metadata = {
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "estimated_cost_usd": response.estimated_cost_usd,
        }
        if response.optimization:
            metadata["original_input_tokens"] = response.optimization.get("original_tokens", response.input_tokens)
            metadata["saved_tokens"] = response.optimization.get("saved_tokens", 0)
            
        self.log_event(event, agent_id, session_id, response.violations, metadata)

    def read_logs(self, tail: int = 50) -> list[dict]:
        path = self._log_path()
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
        return records[-tail:]
