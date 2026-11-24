"""The real clock. The only place wall time comes from outside the tests."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")


class SystemClock:
    """UTC for storage, Madrid for the rules that depend on the hour of the city."""

    def now(self) -> datetime:
        return datetime.now(tz=UTC)

    def madrid_hour(self) -> int:
        return self.now().astimezone(MADRID).hour
