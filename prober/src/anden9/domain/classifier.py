"""Maps one HTTP observation to a check result.

Order matters and is part of the contract: a block is recognised before an error, an error
before a payload problem, and a payload problem before slowness. A ``down`` only stands when
the control endpoint answered in the same minute, see :func:`gate_on_control`.
"""

from __future__ import annotations

from enum import StrEnum

from anden9.domain.bot_page import is_bot_page
from anden9.domain.outcome import AVAILABLE, CheckResult, Outcome, Reason
from anden9.domain.ports import HttpError, HttpResponse
from anden9.domain.spec import ProbeSpec

FORBIDDEN = 403
TOO_MANY_REQUESTS = 429
BLOCKED_REASONS = {FORBIDDEN: Reason.HTTP_403, TOO_MANY_REQUESTS: Reason.HTTP_429}
SERVER_ERROR_STATUS = 500


class Payload(StrEnum):
    """What a probe concluded about the body it received."""

    VALID = "valid"
    EMPTY = "empty"
    INVALID = "invalid"


def classify(response: HttpResponse, spec: ProbeSpec, *, payload: Payload) -> CheckResult:
    """Classify a response, given the probe's verdict on its payload."""
    status = response.status
    elapsed = response.elapsed_ms
    blocked_reason = BLOCKED_REASONS.get(status)
    if blocked_reason is not None:
        return CheckResult(Outcome.BLOCKED, blocked_reason, status, elapsed)
    if is_bot_page(response):
        return CheckResult(Outcome.BLOCKED, Reason.BOT_PAGE, status, elapsed)
    if status >= SERVER_ERROR_STATUS:
        return CheckResult(Outcome.DOWN, Reason.HTTP_5XX, status, elapsed)
    if payload is Payload.INVALID:
        return CheckResult(Outcome.DOWN, Reason.BAD_SHAPE, status, elapsed)
    if payload is Payload.EMPTY:
        return CheckResult(Outcome.DEGRADED, Reason.EMPTY, status, elapsed)
    if elapsed > spec.degraded_ms:
        return CheckResult(Outcome.DEGRADED, Reason.SLOW, status, elapsed)
    return CheckResult(Outcome.UP, Reason.OK, status, elapsed)


def classify_failure(error: HttpError, spec: ProbeSpec) -> CheckResult:
    """Classify a request that never produced a response."""
    return CheckResult(Outcome.DOWN, error.reason, None, spec.timeout_ms)


def classify_probe_error(spec: ProbeSpec) -> CheckResult:
    """The prober itself broke, which is never evidence about Renfe."""
    return CheckResult(Outcome.UNKNOWN, Reason.PROBE_ERROR, None, spec.timeout_ms)


def gate_on_control(result: CheckResult, control: CheckResult | None) -> CheckResult:
    """Keep a ``down`` only if the control endpoint answered; otherwise the fault may be ours.

    ``control`` is ``None`` when no control check exists for that minute, which is treated
    exactly like a failed control: without proof that our own network works, a failure is
    not published against Renfe.
    """
    if result.outcome is not Outcome.DOWN:
        return result
    if control is not None and control.outcome in AVAILABLE:
        return result
    return CheckResult(
        Outcome.UNKNOWN, Reason.CONTROL_FAILED, result.http_status, result.duration_ms
    )
