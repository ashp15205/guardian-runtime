"""Local filesystem storage for usage tracking (analytics only)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

GUARDIAN_RUNTIME_DIR = Path.home() / ".guardian_runtime"
USAGE_FILE = GUARDIAN_RUNTIME_DIR / "usage.json"


class LocalStorage:
    """Reads/writes ~/.guardian_runtime/usage.json for analytics tracking."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or GUARDIAN_RUNTIME_DIR
        self.usage_file = self.base_dir / "usage.json"

    def increment_usage(self) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = {"month": today, "checks": 0}

        if self.usage_file.exists():
            with open(self.usage_file, encoding="utf-8") as f:
                usage = json.load(f)
            if usage.get("month") != today:
                usage = {"month": today, "checks": 0}

        usage["checks"] = int(usage.get("checks", 0)) + 1
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with open(self.usage_file, "w", encoding="utf-8") as f:
            json.dump(usage, f, indent=2)
        return usage["checks"]

    def get_usage(self) -> dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m")
        if not self.usage_file.exists():
            return {"month": today, "checks": 0}
        with open(self.usage_file, encoding="utf-8") as f:
            usage = json.load(f)
        if usage.get("month") != today:
            return {"month": today, "checks": 0}
        return usage
