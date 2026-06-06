"""Local filesystem storage for usage tracking (analytics only)."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

GUARDIAN_RUNTIME_DIR = Path.home() / ".guardian_runtime"
USAGE_FILE = GUARDIAN_RUNTIME_DIR / "usage.json"
HISTORY_FILE = GUARDIAN_RUNTIME_DIR / "history.jsonl"


class LocalStorage:
    """Reads/writes ~/.guardian_runtime/usage.json for analytics tracking."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or GUARDIAN_RUNTIME_DIR
        self.usage_file = self.base_dir / "usage.json"
        self.history_file = self.base_dir / "history.jsonl"

    def increment_usage(self) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        with FileLock(str(self.usage_file) + ".lock", timeout=5):
            usage = {"date": today, "checks": 0, "spend_usd": 0.0}
            if self.usage_file.exists():
                try:
                    with open(self.usage_file, encoding="utf-8") as f:
                        usage = json.load(f)
                    if usage.get("date") != today:
                        usage = {"date": today, "checks": 0, "spend_usd": 0.0}
                except json.JSONDecodeError:
                    pass

            usage["checks"] = int(usage.get("checks", 0)) + 1
            with open(self.usage_file, "w", encoding="utf-8") as f:
                json.dump(usage, f, indent=2)
                
        return usage["checks"]

    def add_spend(self, amount_usd: float) -> float:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        with FileLock(str(self.usage_file) + ".lock", timeout=5):
            usage = {"date": today, "checks": 0, "spend_usd": 0.0}
            if self.usage_file.exists():
                try:
                    with open(self.usage_file, encoding="utf-8") as f:
                        usage = json.load(f)
                    if usage.get("date") != today:
                        usage = {"date": today, "checks": 0, "spend_usd": 0.0}
                except json.JSONDecodeError:
                    pass

            usage["spend_usd"] = float(usage.get("spend_usd", 0.0)) + amount_usd
            with open(self.usage_file, "w", encoding="utf-8") as f:
                json.dump(usage, f, indent=2)
                
        return usage["spend_usd"]

    def get_daily_spend(self) -> float:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not self.usage_file.exists():
            return 0.0
        try:
            with open(self.usage_file, encoding="utf-8") as f:
                usage = json.load(f)
            if usage.get("date") != today:
                return 0.0
            return float(usage.get("spend_usd", 0.0))
        except json.JSONDecodeError:
            return 0.0

    def record_request(self, tool: str, cost_usd: float, tokens: int, blocked: bool, block_reason: str | None = None) -> None:
        """Append a single request event to the history log for analytics."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        with FileLock(str(self.history_file) + ".lock", timeout=5):
            if self.history_file.exists() and self.history_file.stat().st_size > 10 * 1024 * 1024:
                rotated_file = self.history_file.with_name(self.history_file.name + ".1")
                shutil.move(self.history_file, rotated_file)

            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": tool,
                "cost_usd": cost_usd,
                "tokens": tokens,
                "blocked": blocked,
                "block_reason": block_reason
            }
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")

    def get_analytics(self, date_filter: str | None = None) -> dict[str, dict]:
        """Aggregate history events by tool.
        date_filter: 'YYYY-MM-DD' string to filter, or None for all-time.
        """
        analytics: dict[str, dict] = {}
        if not self.history_file.exists():
            return analytics
            
        with open(self.history_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Filter by date if provided
                if date_filter and not event.get("timestamp", "").startswith(date_filter):
                    continue
                    
                tool = event.get("tool", "Unknown")
                if tool not in analytics:
                    analytics[tool] = {
                        "cost": 0.0,
                        "requests": 0,
                        "blocked": 0,
                        "tokens": 0,
                        "block_reasons": {}
                    }
                
                analytics[tool]["requests"] += 1
                analytics[tool]["cost"] += event.get("cost_usd", 0.0)
                analytics[tool]["tokens"] += event.get("tokens", 0)
                
                if event.get("blocked"):
                    analytics[tool]["blocked"] += 1
                    reason = event.get("block_reason") or "Unknown"
                    analytics[tool]["block_reasons"][reason] = analytics[tool]["block_reasons"].get(reason, 0) + 1
                    
        return analytics
