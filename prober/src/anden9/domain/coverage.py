"""Turns a list of checks into whole seconds per state, and names the holes.

A check covers from its own start until the next one starts, capped at twice its nominal interval.
Anything left uncovered is a gap: the prober was not measuring, so the period is `unknown` and it
never counts as uptime, in either direction.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from anden9.domain.outcome import Outcome

MAX_COVER_MULTIPLIER = 2


@dataclass(frozen=True, slots=True)
class ObservedCheck:
    """The only two fields coverage needs."""

    started_at: datetime
    outcome: Outcome


@dataclass(slots=True)
class SecondShares:
    """Whole seconds per state inside one window."""

    by_outcome: dict[Outcome, int] = field(default_factory=dict)

    def add(self, outcome: Outcome, seconds: int) -> None:
        if seconds > 0:
            self.by_outcome[outcome] = self.by_outcome.get(outcome, 0) + seconds

    def of(self, outcome: Outcome) -> int:
        return self.by_outcome.get(outcome, 0)

    @property
    def total(self) -> int:
        return sum(self.by_outcome.values())


def cover(
    checks: Sequence[ObservedCheck],
    *,
    interval_s: int,
    window_start: datetime,
    window_end: datetime,
) -> SecondShares:
    """Attribute every second of the window to a state, gaps included."""
    shares = SecondShares()
    if window_end <= window_start:
        return shares

    ordered = sorted(checks, key=lambda check: check.started_at)
    cap = timedelta(seconds=interval_s * MAX_COVER_MULTIPLIER)
    cursor = window_start

    for index, check in enumerate(ordered):
        start = max(check.started_at, window_start)
        stop = check.started_at + cap
        if index + 1 < len(ordered):
            stop = min(stop, ordered[index + 1].started_at)
        stop = min(stop, window_end)
        if stop <= window_start or start >= window_end:
            continue
        if start > cursor:
            shares.add(Outcome.UNKNOWN, int((start - cursor).total_seconds()))
            cursor = start
        if stop > cursor:
            shares.add(check.outcome, int((stop - cursor).total_seconds()))
            cursor = stop

    if cursor < window_end:
        shares.add(Outcome.UNKNOWN, int((window_end - cursor).total_seconds()))
    return shares
