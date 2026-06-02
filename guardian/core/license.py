"""License validation — offline-first with optional daily sync."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx

from guardian.core.storage import LocalStorage


class LicenseManager:
    """Validates license locally; optionally syncs check count to a server."""

    def __init__(self, storage: LocalStorage | None = None) -> None:
        self.storage = storage or LocalStorage()
        self.sync_url = os.environ.get("GUARDIAN_LICENSE_URL", "").strip()

    def check_or_sync(self) -> bool:
        """Return True if usage is allowed. Syncs when URL is configured."""
        allowed, _, _ = self.storage.check_usage_limit()
        if self.sync_url:
            self.sync_with_server()
        return allowed

    def sync_with_server(self) -> None:
        """POST license key + monthly check count to validation server."""
        config = self.storage.load_license()
        if not config or not self.sync_url:
            return

        usage = self.storage.get_usage()
        payload = {
            "license_key": config.get("license_key"),
            "checks_used": usage.get("checks", 0),
        }
        try:
            httpx.post(self.sync_url, json=payload, timeout=10.0)
            self.storage.mark_synced(datetime.now(timezone.utc).isoformat())
        except httpx.HTTPError:
            pass  # offline-first: sync failure must not block local usage

    def is_initialized(self) -> bool:
        return self.storage.load_license() is not None
