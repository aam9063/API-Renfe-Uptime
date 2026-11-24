"""Maps one HTTP observation to a check result.

A probe answers whether the payload was valid, empty or invalid, and this module decides the
outcome. Bot page detection can only move a would-be `down` to `blocked`, which never lowers the
published uptime: when the answer looks like a protection page we say we do not know how a real
user saw the service, instead of publishing an outage we cannot prove.
"""

from __future__ import annotations

from enum import StrEnum

from anden9.domain.outcome import CheckResult, Outcome, Reason
from anden9.domain.ports import HttpError, HttpResponse
from anden9.domain.spec import ProbeSpec

FORBIDDEN = 403
TOO_MANY_REQUESTS = 429
BLOCKED_REASONS = {FORBIDDEN: Reason.HTTP_403, TOO_MANY_REQUESTS: Reason.HTTP_429}
SERVER_ERROR_STATUS = 500

BOT_PAGE_MARKERS = (
    b"captcha",
    b"are you a robot",
    b"access denied",
    b"request blocked",
    b"requests blocked",
    b"sala de espera",
    b"queue-it",
    b"incapsula",
    b"cloudflare",
    b"attention required",
)


class PayloadState(StrEnum):
    """What a probe thinks of the bytes it received."""

    VALID = "valid"
    EMPTY = "empty"
    INVALID = "invalid"


def looks_like_bot_page(body: bytes) -> bool:
    lowered = body.lower()
    return any(marker in lowered for marker in BOT_PAGE_MARKERS)


def classify(response: HttpResponse, spec: ProbeSpec, *, payload: PayloadState) -> CheckResult:
    """Classify a response, given the probe's verdict on its payload."""
    outcome, reason = _decide(response, spec, payload)
    return CheckResult(outcome, reason, response.status, response.elapsed_ms)


def _decide(
    response: HttpResponse,
    spec: ProbeSpec,
    payload: PayloadState,
) -> tuple[Outcome, Reason]:
    blocked_reason = BLOCKED_REASONS.get(response.status)
    if blocked_reason is not None:
        return Outcome.BLOCKED, blocked_reason
    if response.status >= SERVER_ERROR_STATUS:
        return Outcome.DOWN, Reason.HTTP_5XX
    if payload is PayloadState.INVALID:
        return _invalid_payload(response)
    if payload is PayloadState.EMPTY:
        return Outcome.DEGRADED, Reason.EMPTY
    if response.elapsed_ms > spec.degraded_ms:
        return Outcome.DEGRADED, Reason.SLOW
    return Outcome.UP, Reason.OK


def _invalid_payload(response: HttpResponse) -> tuple[Outcome, Reason]:
    if looks_like_bot_page(response.body):
        return Outcome.BLOCKED, Reason.BOT_PAGE
    return Outcome.DOWN, Reason.BAD_SHAPE


def classify_failure(error: HttpError, spec: ProbeSpec) -> CheckResult:
    """Classify a request that never produced a response."""
    return CheckResult(Outcome.DOWN, error.reason, None, spec.timeout_ms)


def classify_probe_error(spec: ProbeSpec) -> CheckResult:
    """The prober itself broke, which is never evidence about Renfe."""
    return CheckResult(Outcome.UNKNOWN, Reason.PROBE_ERROR, None, spec.timeout_ms)


def apply_control_gate(result: CheckResult, *, control_ok: bool) -> CheckResult:
    """A `down` only counts when the network itself was proven healthy in the same minute."""
    if result.outcome is Outcome.DOWN and not control_ok:
        return CheckResult(
            Outcome.UNKNOWN,
            Reason.CONTROL_FAILED,
            result.http_status,
            result.duration_ms,
        )
    return result
