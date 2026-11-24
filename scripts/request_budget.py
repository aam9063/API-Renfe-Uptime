"""Fails when the catalog asks Renfe for more, or more often, than the budget allows."""

from __future__ import annotations

import sys

from anden9.domain.budget import MAX_REQUESTS_PER_HOUR, BudgetError, validate
from anden9.probes.catalog import budget_entries


def main() -> int:
    try:
        total = validate(budget_entries())
    except BudgetError as error:
        sys.stdout.write(f"FAIL request budget: {error}\n")
        return 1
    sys.stdout.write(
        f"OK request budget: {total} requests per hour to Renfe "
        f"(limit {MAX_REQUESTS_PER_HOUR}, control endpoint excluded)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
