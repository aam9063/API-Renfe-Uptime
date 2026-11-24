"""The catalog must stay polite: this is the test that fails when it does not."""

from __future__ import annotations

import pytest

from anden9.domain.budget import (
    MAX_REQUESTS_PER_HOUR,
    BudgetEntry,
    BudgetError,
    requests_per_hour,
    validate,
)
from anden9.probes.catalog import budget_entries


def test_real_catalog_matches_the_budget_of_the_brief() -> None:
    assert validate(budget_entries()) == 116
    assert validate(budget_entries()) < MAX_REQUESTS_PER_HOUR


def test_interval_below_one_minute_is_rejected() -> None:
    with pytest.raises(BudgetError, match="below the 60s floor"):
        validate([BudgetEntry("too-fast", interval_s=30)])


def test_heavy_probe_below_fifteen_minutes_is_rejected() -> None:
    with pytest.raises(BudgetError, match="heavy probe"):
        validate([BudgetEntry("heavy-too-fast", interval_s=300, heavy=True)])


def test_catalog_over_the_hourly_limit_is_rejected() -> None:
    entries = [BudgetEntry(f"probe-{index}", interval_s=60) for index in range(5)]
    with pytest.raises(BudgetError, match="budget is 150"):
        validate(entries)


def test_requests_per_hour_counts_every_request_of_a_run() -> None:
    entries = [BudgetEntry("two-per-run", interval_s=900, requests_per_run=2)]
    assert requests_per_hour(entries) == 8


def test_a_failing_probe_never_costs_more_than_the_budget() -> None:
    """A 30s interval on top of the real catalog must be rejected, not silently accepted."""
    entries = (*budget_entries(), BudgetEntry("intruder", interval_s=30))
    with pytest.raises(BudgetError):
        validate(entries)
