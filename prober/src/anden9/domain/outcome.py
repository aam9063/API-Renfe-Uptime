"""The vocabulary every measurement is expressed in."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Outcome(StrEnum):
    """The five states a single check can have."""

    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class Reason(StrEnum):
    """Stable machine-readable cause attached to a check.

    ``OK`` marks a check that found the service healthy, so every stored check
    carries a reason and grouping by reason never needs a null case.
    """

    OK = "ok"
    TIMEOUT = "timeout"
    CONN_REFUSED = "conn_refused"
    DNS = "dns"
    TLS = "tls"
    HTTP_5XX = "http_5xx"
    BAD_SHAPE = "bad_shape"
    SLOW = "slow"
    EMPTY = "empty"
    HTTP_403 = "http_403"
    HTTP_429 = "http_429"
    BOT_PAGE = "bot_page"
    CONTROL_FAILED = "control_failed"
    PROBE_ERROR = "probe_error"
    GAP = "gap"


AVAILABLE = frozenset({Outcome.UP, Outcome.DEGRADED})
EXCLUDED_FROM_DENOMINATOR = frozenset({Outcome.BLOCKED, Outcome.UNKNOWN})


@dataclass(frozen=True, slots=True)
class CheckResult:
    """One probe observation, ready to be stored and aggregated."""

    outcome: Outcome
    reason: Reason
    http_status: int | None
    duration_ms: int
    retry_after_s: int | None = None

    def counts_as_available(self) -> bool:
        return self.outcome in AVAILABLE

    def counts_in_denominator(self) -> bool:
        return self.outcome not in EXCLUDED_FROM_DENOMINATOR
