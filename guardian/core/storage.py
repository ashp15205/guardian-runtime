"""Local filesystem storage for license and usage tracking."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

GUARDIAN_DIR = Path.home() / ".guardian"
CONFIG_FILE = GUARDIAN_DIR / "config.json"
USAGE_FILE = GUARDIAN_DIR / "usage.json"

DEFAULT_FREE_LIMIT = 10_000


class LocalStorage:
    """Reads/writes ~/.guardian/config.json and usage.json."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or GUARDIAN_DIR
        self.config_file = self.base_dir / "config.json"
        self.usage_file = self.base_dir / "usage.json"

    def save_license(
        self,
        key: str,
        plan: str = "free",
        limit: int = DEFAULT_FREE_LIMIT,
        expiry: str | None = None,
    ) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "license_key": key,
            "plan": plan,
            "check_limit": limit,
            "expiry": expiry,
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load_license(self) -> dict | None:
        if not self.config_file.exists():
            return None
        with open(self.config_file, encoding="utf-8") as f:
            return json.load(f)

    def increment_usage(self) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = {"month": today, "checks": 0, "last_sync": None}

        if self.usage_file.exists():
            with open(self.usage_file, encoding="utf-8") as f:
                usage = json.load(f)
            if usage.get("month") != today:
                usage = {"month": today, "checks": 0, "last_sync": usage.get("last_sync")}

        usage["checks"] = int(usage.get("checks", 0)) + 1
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with open(self.usage_file, "w", encoding="utf-8") as f:
            json.dump(usage, f, indent=2)
        return usage["checks"]

    def get_usage(self) -> dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m")
        if not self.usage_file.exists():
            return {"month": today, "checks": 0, "last_sync": None}
        with open(self.usage_file, encoding="utf-8") as f:
            usage = json.load(f)
        if usage.get("month") != today:
            return {"month": today, "checks": 0, "last_sync": usage.get("last_sync")}
        return usage

    def check_usage_limit(self) -> tuple[bool, int, int]:
        """Return (allowed, checks_used, check_limit)."""
        config = self.load_license() or {}
        limit = int(config.get("check_limit", DEFAULT_FREE_LIMIT))
        used = int(self.get_usage().get("checks", 0))
        return used < limit, used, limit

    def mark_synced(self, timestamp: str) -> None:
        usage = self.get_usage()
        usage["last_sync"] = timestamp
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with open(self.usage_file, "w", encoding="utf-8") as f:
            json.dump(usage, f, indent=2)
