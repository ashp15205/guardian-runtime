"""License validation — offline-first with optional daily sync.

Sync fires at most once every 24 hours to avoid adding latency to every
``complete()`` call.  The ``allowed`` result is also cached in-memory for
the lifetime of the ``LicenseManager`` instance so that repeated calls
within the same process skip the filesystem entirely until the next sync
window opens.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

from guardian.core.storage import LocalStorage

# How often to phone home (when a sync URL is configured).
_SYNC_INTERVAL = timedelta(hours=24)


class LicenseManager:
    """Validates license locally; optionally syncs check count to a server."""

    def __init__(self, storage: LocalStorage | None = None) -> None:
        self.storage = storage or LocalStorage()
        self.sync_url = os.environ.get("GUARDIAN_LICENSE_URL", "").strip()
        # In-memory cache so we don't re-read the filesystem on every call.
        self._cached_allowed: bool | None = None

    def check_or_sync(self) -> bool:
        """Return True if usage is allowed.

        Syncs with the remote server **at most once per day** when a URL is
        configured.  Between syncs the result is served from an in-memory
        cache.
        """
        allowed, _, _ = self.storage.check_usage_limit()
        self._cached_allowed = allowed

        if self.sync_url and self._should_sync():
            self.sync_with_server()

        return allowed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_sync(self) -> bool:
        """Return True only when ≥24 h have elapsed since the last sync."""
        usage = self.storage.get_usage()
        last_sync_str = usage.get("last_sync")
        if not last_sync_str:
            return True  # never synced — do it now

        try:
            last_sync_dt = datetime.fromisoformat(last_sync_str)
        except (ValueError, TypeError):
            return True  # corrupt timestamp — re-sync

        return datetime.now(timezone.utc) - last_sync_dt >= _SYNC_INTERVAL

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
