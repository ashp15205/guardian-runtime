"""Local ~/.guardian/ file manager — config.json and usage.json."""
from __future__ import annotations  # Python 3.9 compatibility
# TODO (Week 6): Implement LocalStorage
# See ARCHITECTURE.md §4.8 for full spec


class LocalStorage:
    """Manages ~/.guardian/config.json and ~/.guardian/usage.json."""

    def save_license(self, key: str, plan: str, limit: int, expiry: str | None = None):
        raise NotImplementedError

    def load_license(self) -> dict | None:
        raise NotImplementedError

    def increment_usage(self) -> int:
        raise NotImplementedError

    def get_usage(self) -> dict:
        raise NotImplementedError

    def check_usage_limit(self) -> tuple[bool, int, int]:
        """Returns (within_limit, current_count, plan_limit)."""
        raise NotImplementedError

    def mark_synced(self, timestamp: str):
        raise NotImplementedError
