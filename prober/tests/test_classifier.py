"""The status, payload and latency rules of the classifier, pinned one by one."""

from __future__ import annotations

from datetime import UTC, datetime

from anden9.domain.classifier import (
    PayloadState,
    apply_control_gate,
    classify,
    classify_failure,
    classify_probe_error,
    looks_like_bot_page,
)
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


def response(status: int, elapsed_ms: int = 100, body: bytes = b"{}") -> HttpResponse:
    return HttpResponse(
        status=status,
        headers={},
        body=body,
        elapsed_ms=elapsed_ms,
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_a_fast_valid_response_is_up() -> None:
    result = classify(response(200), SPEC, payload=PayloadState.VALID)
    assert (result.outcome, result.reason, result.http_status) == (Outcome.UP, Reason.OK, 200)


def test_a_valid_but_slow_response_is_degraded_and_still_available() -> None:
    result = classify(response(200, elapsed_ms=2500), SPEC, payload=PayloadState.VALID)
    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.SLOW)
    assert result.counts_as_available()


def test_an_empty_payload_is_degraded() -> None:
    result = classify(response(200), SPEC, payload=PayloadState.EMPTY)
    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.EMPTY)
    assert result.counts_as_available()


def test_an_invalid_payload_is_down() -> None:
    result = classify(response(200), SPEC, payload=PayloadState.INVALID)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)
    assert result.counts_in_denominator()


def test_server_errors_are_down() -> None:
    result = classify(response(503), SPEC, payload=PayloadState.INVALID)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.HTTP_5XX)


def test_forbidden_is_blocked_and_excluded() -> None:
    result = classify(response(403), SPEC, payload=PayloadState.INVALID)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.HTTP_403)
    assert not result.counts_in_denominator()


def test_too_many_requests_is_blocked_and_excluded() -> None:
    result = classify(response(429), SPEC, payload=PayloadState.INVALID)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.HTTP_429)


def test_a_protection_page_is_blocked_never_down() -> None:
    body = b"<html><body>Please solve this CAPTCHA to continue</body></html>"
    result = classify(response(200, body=body), SPEC, payload=PayloadState.INVALID)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.BOT_PAGE)
    assert not result.counts_as_available()
    assert not result.counts_in_denominator()


def test_an_error_page_without_bot_markers_is_still_down() -> None:
    body = b"<html><body>Error 500 en la aplicacion</body></html>"
    result = classify(response(200, body=body), SPEC, payload=PayloadState.INVALID)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)


def test_bot_marker_detection_is_case_insensitive() -> None:
    assert looks_like_bot_page(b"Attention Required! | CloudFlare")
    assert not looks_like_bot_page(b'{"arch": {}}')


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


def test_a_down_is_downgraded_to_unknown_when_the_control_endpoint_also_fails() -> None:
    down = classify(response(503), SPEC, payload=PayloadState.INVALID)
    gated = apply_control_gate(down, control_ok=False)
    assert (gated.outcome, gated.reason) == (Outcome.UNKNOWN, Reason.CONTROL_FAILED)
    assert not gated.counts_in_denominator()


def test_the_control_gate_leaves_a_down_alone_when_the_network_is_healthy() -> None:
    down = classify(response(503), SPEC, payload=PayloadState.INVALID)
    assert apply_control_gate(down, control_ok=True) == down


def test_the_control_gate_never_touches_an_available_check() -> None:
    up = classify(response(200), SPEC, payload=PayloadState.VALID)
    assert apply_control_gate(up, control_ok=False) == up
