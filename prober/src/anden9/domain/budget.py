"""How polite a catalog is to Renfe, computed from the catalog and never guessed."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

SECONDS_PER_HOUR = 3600
MIN_INTERVAL_S = 60
MIN_HEAVY_INTERVAL_S = 900
MAX_REQUESTS_PER_HOUR = 150


class BudgetError(ValueError):
    """The catalog asks Renfe for more requests, or more often, than allowed."""


@dataclass(frozen=True, slots=True)
class BudgetEntry:
    """The only fields the budget depends on, so a test can lie about them."""

    probe_id: str
    interval_s: int
    requests_per_run: int = 1
    heavy: bool = False


def runs_per_hour(interval_s: int) -> int:
    """Whole runs that fit in an hour, rounded up so the answer never flatters us."""
    return -(-SECONDS_PER_HOUR // interval_s)


def requests_per_hour(entries: Iterable[BudgetEntry]) -> int:
    return sum(runs_per_hour(entry.interval_s) * entry.requests_per_run for entry in entries)


def validate(entries: Sequence[BudgetEntry], *, limit: int = MAX_REQUESTS_PER_HOUR) -> int:
    """Reject a catalog that is too fast or too heavy, and return its hourly total."""
    for entry in entries:
        if entry.interval_s < MIN_INTERVAL_S:
            message = f"{entry.probe_id}: {entry.interval_s}s is below the {MIN_INTERVAL_S}s floor"
            raise BudgetError(message)
        if entry.heavy and entry.interval_s < MIN_HEAVY_INTERVAL_S:
            message = (
                f"{entry.probe_id}: heavy probe at {entry.interval_s}s, "
                f"the floor is {MIN_HEAVY_INTERVAL_S}s"
            )
            raise BudgetError(message)
    total = requests_per_hour(entries)
    if total > limit:
        message = f"catalog needs {total} requests per hour, the budget is {limit}"
        raise BudgetError(message)
    return total
