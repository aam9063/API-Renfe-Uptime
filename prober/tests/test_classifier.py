"""The status and latency rules of the classifier, pinned one by one."""

from __future__ import annotations

from datetime import UTC, datetime

from anden9.domain.classifier import classify, classify_failure, classify_probe_error
from anden9.domain.outcome import Outcome, Reason
from anden9.domain.ports import HttpError, HttpResponse
from anden9.domain.spec import ProbeSpec

SPEC = ProbeSpec(
    probe_id="example",
    module="example",
    name="Example",
    group="test",
    host="example.test",
    method="GET",
    url="https://example.test/",
    interval_s=60,
    timeout_s=10.0,
    degraded_ms=2000,
)


def response(status: int, elapsed_ms: int = 100) -> HttpResponse:
    return HttpResponse(
        status=status,
        headers={},
        body=b"{}",
        elapsed_ms=elapsed_ms,
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_a_fast_valid_response_is_up() -> None:
    result = classify(response(200), SPEC, payload_valid=True)
    assert (result.outcome, result.reason, result.http_status) == (Outcome.UP, Reason.OK, 200)


def test_a_valid_but_slow_response_is_degraded_and_still_available() -> None:
    result = classify(response(200, elapsed_ms=2500), SPEC, payload_valid=True)
    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.SLOW)
    assert result.counts_as_available()


def test_an_invalid_payload_is_down() -> None:
    result = classify(response(200), SPEC, payload_valid=False)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)
    assert result.counts_in_denominator()


def test_server_errors_are_down() -> None:
    result = classify(response(503), SPEC, payload_valid=False)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.HTTP_5XX)


def test_forbidden_is_blocked_and_excluded() -> None:
    result = classify(response(403), SPEC, payload_valid=False)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.HTTP_403)
    assert not result.counts_in_denominator()
    assert not result.counts_as_available()


def test_too_many_requests_is_blocked_and_excluded() -> None:
    result = classify(response(429), SPEC, payload_valid=False)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.HTTP_429)
    assert not result.counts_in_denominator()


def test_a_timeout_is_down_without_a_status() -> None:
    result = classify_failure(HttpError(Reason.TIMEOUT), SPEC)
    assert (result.outcome, result.reason, result.http_status) == (
        Outcome.DOWN,
        Reason.TIMEOUT,
        None,
    )


def test_a_broken_prober_is_unknown_and_excluded() -> None:
    result = classify_probe_error(SPEC)
    assert (result.outcome, result.reason) == (Outcome.UNKNOWN, Reason.PROBE_ERROR)
    assert not result.counts_in_denominator()
