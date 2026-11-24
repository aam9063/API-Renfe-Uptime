"""Maps one HTTP observation to a check result.

The status and latency rules live here. The per-probe payload rules, the control
endpoint gate and the interval coverage arrive with their own tests in M1 and M2.
"""

from __future__ import annotations

from anden9.domain.outcome import CheckResult, Outcome, Reason
from anden9.domain.ports import HttpError, HttpResponse
from anden9.domain.spec import ProbeSpec

FORBIDDEN = 403
TOO_MANY_REQUESTS = 429
BLOCKED_REASONS = {FORBIDDEN: Reason.HTTP_403, TOO_MANY_REQUESTS: Reason.HTTP_429}
SERVER_ERROR_STATUS = 500


def classify(response: HttpResponse, spec: ProbeSpec, *, payload_valid: bool) -> CheckResult:
    """Classify a response, given whether the probe accepted its payload."""
    blocked_reason = BLOCKED_REASONS.get(response.status)
    if blocked_reason is not None:
        return CheckResult(Outcome.BLOCKED, blocked_reason, response.status, response.elapsed_ms)
    if response.status >= SERVER_ERROR_STATUS:
        return CheckResult(Outcome.DOWN, Reason.HTTP_5XX, response.status, response.elapsed_ms)
    if not payload_valid:
        return CheckResult(Outcome.DOWN, Reason.BAD_SHAPE, response.status, response.elapsed_ms)
    if response.elapsed_ms > spec.degraded_ms:
        return CheckResult(Outcome.DEGRADED, Reason.SLOW, response.status, response.elapsed_ms)
    return CheckResult(Outcome.UP, Reason.OK, response.status, response.elapsed_ms)


def classify_failure(error: HttpError, spec: ProbeSpec) -> CheckResult:
    """Classify a request that never produced a response."""
    return CheckResult(Outcome.DOWN, error.reason, None, spec.timeout_ms)


def classify_probe_error(spec: ProbeSpec) -> CheckResult:
    """The prober itself broke, which is never evidence about Renfe."""
    return CheckResult(Outcome.UNKNOWN, Reason.PROBE_ERROR, None, spec.timeout_ms)
