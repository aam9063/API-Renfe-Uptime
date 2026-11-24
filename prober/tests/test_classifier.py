"""The status and latency rules of the classifier, pinned one by one."""

from __future__ import annotations

from datetime import UTC, datetime

from anden9.domain.classifier import (
    Payload,
    classify,
    classify_failure,
    classify_probe_error,
    gate_on_control,
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


def response(status: int, elapsed_ms: int = 100) -> HttpResponse:
    return HttpResponse(
        status=status,
        headers={},
        body=b"{}",
        elapsed_ms=elapsed_ms,
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_a_fast_valid_response_is_up() -> None:
    result = classify(response(200), SPEC, payload=Payload.VALID)
    assert (result.outcome, result.reason, result.http_status) == (Outcome.UP, Reason.OK, 200)


def test_a_valid_but_slow_response_is_degraded_and_still_available() -> None:
    result = classify(response(200, elapsed_ms=2500), SPEC, payload=Payload.VALID)
    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.SLOW)
    assert result.counts_as_available()


def test_an_invalid_payload_is_down() -> None:
    result = classify(response(200), SPEC, payload=Payload.INVALID)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)
    assert result.counts_in_denominator()


def test_server_errors_are_down() -> None:
    result = classify(response(503), SPEC, payload=Payload.INVALID)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.HTTP_5XX)


def test_forbidden_is_blocked_and_excluded() -> None:
    result = classify(response(403), SPEC, payload=Payload.INVALID)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.HTTP_403)
    assert not result.counts_in_denominator()
    assert not result.counts_as_available()


def test_too_many_requests_is_blocked_and_excluded() -> None:
    result = classify(response(429), SPEC, payload=Payload.INVALID)
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


def html(status: int, body: str, elapsed_ms: int = 100) -> HttpResponse:
    return HttpResponse(
        status=status,
        headers={"content-type": "text/html; charset=utf-8"},
        body=body.encode(),
        elapsed_ms=elapsed_ms,
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


QUEUE_PAGE = '<html><script src="https://static.queue-it.net/script/queueclient.min.js"></script>'
AKAMAI_DENIED = (
    "<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY>Reference #18.1"
    " https://errors.edgesuite.net/18.1</BODY></HTML>"
)


def test_a_waiting_room_is_blocked_even_with_a_200() -> None:
    result = classify(html(200, QUEUE_PAGE), SPEC, payload=Payload.INVALID)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.BOT_PAGE)


def test_a_protection_page_behind_a_5xx_is_blocked_not_down() -> None:
    result = classify(html(503, AKAMAI_DENIED), SPEC, payload=Payload.INVALID)
    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.BOT_PAGE)


def test_a_plain_html_error_page_on_a_json_endpoint_is_down() -> None:
    result = classify(html(200, "<html><h1>Error</h1></html>"), SPEC, payload=Payload.INVALID)
    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)


def test_a_station_page_mentioning_a_waiting_room_is_not_a_block() -> None:
    page = "<html><p>La estación dispone de sala de espera y consigna.</p></html>"
    result = classify(html(200, page), SPEC, payload=Payload.VALID)
    assert result.outcome is Outcome.UP


def test_empty_data_is_degraded_and_available() -> None:
    result = classify(response(200), SPEC, payload=Payload.EMPTY)
    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.EMPTY)
    assert result.counts_as_available()


def test_a_down_with_a_healthy_control_stands() -> None:
    down = classify_failure(HttpError(Reason.CONN_REFUSED), SPEC)
    control = classify(response(204), SPEC, payload=Payload.VALID)
    assert gate_on_control(down, control) == down


def test_a_down_with_a_failed_control_is_unknown() -> None:
    down = classify_failure(HttpError(Reason.TIMEOUT), SPEC)
    control = classify_failure(HttpError(Reason.DNS), SPEC)
    gated = gate_on_control(down, control)
    assert (gated.outcome, gated.reason) == (Outcome.UNKNOWN, Reason.CONTROL_FAILED)
    assert not gated.counts_in_denominator()


def test_a_down_without_any_control_check_is_unknown() -> None:
    down = classify(response(502), SPEC, payload=Payload.INVALID)
    gated = gate_on_control(down, None)
    assert (gated.outcome, gated.reason, gated.http_status) == (
        Outcome.UNKNOWN,
        Reason.CONTROL_FAILED,
        502,
    )


def test_the_control_gate_never_touches_other_outcomes() -> None:
    for status in (200, 403, 429):
        result = classify(response(status), SPEC, payload=Payload.VALID)
        assert gate_on_control(result, None) == result
