"""Reference implementation of the uptime formula, used as the oracle of the contract cases.

The published numbers come from the SQL views (``supabase/migrations``). This module exists
so the same rules can be property-tested without a database, and so
``contracts/uptime_cases.json`` is checked against two independent implementations.

All arithmetic is on integers or exact fractions: whole seconds in, basis points (hundredths
of a percent, truncated) and nines out. No float ever decides a published digit.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from fractions import Fraction

from anden9.domain.outcome import Outcome

BASIS_POINTS = 10_000
COVERAGE_FACTOR = 2
MIN_DENOMINATOR_SHARE = Fraction(1, 2)
ONE_SECOND = timedelta(seconds=1)


class WindowStatus(StrEnum):
    OK = "ok"
    NO_DOWNTIME = "no_downtime"
    INSUFFICIENT = "insufficient"
    NO_DATA = "no_data"


@dataclass(frozen=True, slots=True)
class Seconds:
    """Whole seconds of a window, split by state. ``unknown`` includes uncovered gaps."""

    up: int = 0
    degraded: int = 0
    down: int = 0
    blocked: int = 0
    unknown: int = 0

    @property
    def available(self) -> int:
        return self.up + self.degraded

    @property
    def denominator(self) -> int:
        return self.up + self.degraded + self.down

    @property
    def total(self) -> int:
        return self.denominator + self.blocked + self.unknown

    def add(self, outcome: Outcome, seconds: int) -> Seconds:
        return Seconds(
            up=self.up + (seconds if outcome is Outcome.UP else 0),
            degraded=self.degraded + (seconds if outcome is Outcome.DEGRADED else 0),
            down=self.down + (seconds if outcome is Outcome.DOWN else 0),
            blocked=self.blocked + (seconds if outcome is Outcome.BLOCKED else 0),
            unknown=self.unknown + (seconds if outcome is Outcome.UNKNOWN else 0),
        )


@dataclass(frozen=True, slots=True)
class TimedCheck:
    """A stored check reduced to what coverage needs. ``started_at`` has whole seconds."""

    started_at: datetime
    outcome: Outcome
    interval_s: int


@dataclass(frozen=True, slots=True)
class Metrics:
    status: WindowStatus
    uptime_bp: int | None
    nines: int | None


def _whole_seconds(delta: timedelta) -> int:
    return delta // ONE_SECOND


def cover(checks: Sequence[TimedCheck], start: datetime, end: datetime) -> Seconds:
    """Split ``[start, end)`` by state.

    Each check covers from its start until the next check, at most ``2 x interval``. What no
    check covers is ``unknown`` (reason ``gap``). A check that started before the window still
    covers the part of it that falls inside.
    """
    ordered = sorted(checks, key=lambda check: check.started_at)
    seconds = Seconds()
    covered = 0
    for index, check in enumerate(ordered):
        limit = check.started_at + timedelta(seconds=COVERAGE_FACTOR * check.interval_s)
        if index + 1 < len(ordered):
            limit = min(limit, ordered[index + 1].started_at)
        segment_start = max(check.started_at, start)
        segment_end = min(limit, end)
        if segment_end <= segment_start:
            continue
        length = _whole_seconds(segment_end - segment_start)
        seconds = seconds.add(check.outcome, length)
        covered += length
    window = _whole_seconds(end - start)
    return seconds.add(Outcome.UNKNOWN, window - covered)


def nines_of(downtime: Fraction) -> int:
    """Largest ``n`` with ``downtime * 10^n <= 1``, i.e. ``floor(-log10(downtime))`` exactly."""
    nines = 0
    while downtime * 10 ** (nines + 1) <= 1:
        nines += 1
    return nines


def window_metrics(seconds: Seconds, window_s: int) -> Metrics:
    """Uptime and nines of one service over one window."""
    denominator = seconds.denominator
    if denominator == 0:
        return Metrics(WindowStatus.NO_DATA, None, None)
    if Fraction(denominator, window_s) < MIN_DENOMINATOR_SHARE:
        return Metrics(WindowStatus.INSUFFICIENT, None, None)
    uptime_bp = seconds.available * BASIS_POINTS // denominator
    if seconds.down == 0:
        return Metrics(WindowStatus.NO_DOWNTIME, uptime_bp, None)
    return Metrics(WindowStatus.OK, uptime_bp, nines_of(Fraction(seconds.down, denominator)))


def aggregate_metrics(services: Sequence[Seconds], window_s: int) -> Metrics:
    """Equal-weight mean of the services whose window has enough data."""
    usable = [
        seconds
        for seconds in services
        if window_metrics(seconds, window_s).status
        in {WindowStatus.OK, WindowStatus.NO_DOWNTIME}
    ]
    if not usable:
        statuses = {window_metrics(seconds, window_s).status for seconds in services}
        if WindowStatus.INSUFFICIENT in statuses:
            return Metrics(WindowStatus.INSUFFICIENT, None, None)
        return Metrics(WindowStatus.NO_DATA, None, None)
    mean = sum(
        (Fraction(seconds.available, seconds.denominator) for seconds in usable), Fraction(0)
    ) / len(usable)
    uptime_bp = int(mean * BASIS_POINTS)
    if all(seconds.down == 0 for seconds in usable):
        return Metrics(WindowStatus.NO_DOWNTIME, uptime_bp, None)
    return Metrics(WindowStatus.OK, uptime_bp, nines_of(1 - mean))
