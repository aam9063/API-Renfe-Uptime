"""Uptime, nines and truncation as an executable specification.

The SQL views are the runtime truth; this module is the specification the property tests quantify
over and the one the shared contract cases run against. If the two ever disagree, the views win and
this file is fixed.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from anden9.domain.coverage import SecondShares
from anden9.domain.outcome import AVAILABLE, Outcome

MIN_COVERAGE = Fraction(1, 2)
PERCENT = 100
DECIMALS = 2
NINES_UNIT = 10
MAX_NINES = 12
NO_DOWNTIME_LABEL = "sin caídas"
INSUFFICIENT_LABEL = "datos insuficientes"


@dataclass(frozen=True, slots=True)
class UptimeSummary:
    """One window of one probe, or the aggregate of the active ones."""

    window_seconds: int
    available_seconds: int
    denominator_seconds: int
    down_seconds: int
    uptime: Fraction | None
    nines: int | None
    insufficient: bool

    @property
    def no_downtime(self) -> bool:
        return self.denominator_seconds > 0 and self.down_seconds == 0

    @property
    def label(self) -> str | None:
        if self.insufficient:
            return INSUFFICIENT_LABEL
        if self.no_downtime:
            return NO_DOWNTIME_LABEL
        return None


def summarise(shares: SecondShares, *, window_seconds: int) -> UptimeSummary:
    """Apply the formula of the brief to one window of seconds."""
    available = sum(shares.of(outcome) for outcome in AVAILABLE)
    down = shares.of(Outcome.DOWN)
    denominator = available + down
    insufficient = Fraction(denominator, 1) < MIN_COVERAGE * window_seconds
    uptime = Fraction(available, denominator) if denominator > 0 else None
    return UptimeSummary(
        window_seconds=window_seconds,
        available_seconds=available,
        denominator_seconds=denominator,
        down_seconds=down,
        uptime=uptime,
        nines=nines(down, denominator),
        insufficient=insufficient,
    )


def nines(down_seconds: int, denominator_seconds: int) -> int | None:
    """`floor(-log10(1 - uptime))`, or `None` when no second was lost."""
    if down_seconds <= 0 or denominator_seconds <= 0:
        return None
    value = 0
    scale = NINES_UNIT
    while value < MAX_NINES and scale * down_seconds <= denominator_seconds:
        value += 1
        scale *= NINES_UNIT
    return value


def format_percent(uptime: Fraction) -> str:
    """Truncate to two decimals, never round, and use the Spanish comma."""
    scale = NINES_UNIT**DECIMALS
    scaled = int(uptime * PERCENT * scale)
    whole, cents = divmod(scaled, scale)
    return f"{whole},{cents:02d}"
