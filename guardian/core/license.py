"""License key validation and once-daily server sync."""
from __future__ import annotations  # Python 3.9 compatibility
# TODO (Week 6): Implement LicenseManager
# See ARCHITECTURE.md §4.9 for full spec — especially fail-open and grace period logic


class LicenseManager:
    """Validates license locally and syncs with guardian-ai.dev once per day."""

    LICENSE_SERVER_URL = "https://guardian-ai.dev/api/validate"

    def check_or_sync(self):
        """Called before every guardian.complete(). Syncs if >24h since last sync."""
        raise NotImplementedError

    def sync_with_server(self):
        """POST { license_key, checks_used } → receive { valid, plan, limit, expiry }."""
        raise NotImplementedError

    def is_initialized(self) -> bool:
        raise NotImplementedError
