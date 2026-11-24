"""Every probe, against canned answers: what it accepts, what it refuses, what it degrades to."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from anden9.domain.outcome import CheckResult, Outcome, Reason
from anden9.domain.ports import HttpRequest, HttpResponse
from anden9.probes.base import Probe, ProbeContext
from anden9.probes.catalog import CONTROL_ENDPOINT, spec_by_id
from anden9.probes.control import ControlProbe
from anden9.probes.gtfs_avld import GtfsAvldProbe
from anden9.probes.legacy_shop import LegacyShopProbe
from anden9.probes.live_map import LiveMapProbe
from anden9.probes.nsv_config import NsvConfigProbe
from anden9.probes.nsv_search import NsvSearchProbe
from anden9.probes.nsv_stations import NsvStationsProbe
from anden9.probes.nsv_token import NsvTokenProbe
from anden9.probes.session import SessionState
from anden9.probes.www_search import WwwSearchProbe
from fakes import FakeTransport, FixedClock, json_response, response

WARM = SessionState(api_key="key", session_id="session", terminal_id="1")
LEGACY_PAGE = response(200, body=b"<html>buscar</html>")
LEGACY_DWR = response(200, body=b"handleCallback")


@dataclass(frozen=True, slots=True)
class Case:
    name: str
    probe: Probe
    answers: dict[str, list[HttpResponse]] = field(default_factory=dict)
    expected: Outcome = Outcome.UP
    reason: Reason = Reason.OK
    session: SessionState = field(default_factory=lambda: WARM)


def answers(
    *,
    page: HttpResponse | None = None,
    dwr: HttpResponse | None = None,
) -> dict[str, list[HttpResponse]]:
    legacy = spec_by_id("legacy-shop").url
    dwr_url = "https://venta.renfe.com/vol/dwr/call/plaincall/__System.generateId.dwr"
    return {
        legacy: [page or LEGACY_PAGE, dwr or LEGACY_DWR],
        dwr_url: [dwr or LEGACY_DWR],
    }


async def observe(probe: Probe, transport: FakeTransport, session: SessionState) -> CheckResult:
    return await probe.run(
        ProbeContext(
            spec=spec_by_id(probe.probe_id),
            http=transport,
            clock=FixedClock(),
            session=session,
        )
    )


async def test_nsv_config_accepts_a_key() -> None:
    body = json_response({"arch": {"security": {"apiKey": "k"}}})
    session = SessionState()
    result = await observe(
        NsvConfigProbe(),
        FakeTransport(answers={spec_by_id("nsv-config").url: [body]}),
        session,
    )

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)
    assert session.api_key == "k"


async def test_nsv_config_records_the_key_even_when_the_answer_is_just_valid() -> None:
    body = json_response({"arch": {"security": {"apiKey": ""}}})
    result = await observe(
        NsvConfigProbe(),
        FakeTransport(answers={spec_by_id("nsv-config").url: [body]}),
        SessionState(),
    )

    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)


async def test_a_protection_page_is_blocked() -> None:
    body = response(200, body=b"<html>please solve this captcha</html>")
    result = await observe(
        NsvConfigProbe(),
        FakeTransport(answers={spec_by_id("nsv-config").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.BLOCKED, Reason.BOT_PAGE)


async def test_a_server_error_is_down() -> None:
    result = await observe(
        NsvConfigProbe(),
        FakeTransport(answers={spec_by_id("nsv-config").url: [response(503)]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.HTTP_5XX)


async def test_a_slow_answer_is_degraded() -> None:
    body = json_response({"arch": {"security": {"apiKey": "k"}}}, elapsed_ms=9000)
    result = await observe(
        NsvConfigProbe(),
        FakeTransport(answers={spec_by_id("nsv-config").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.SLOW)


async def test_the_token_rides_on_the_key_it_already_has() -> None:
    body = json_response({"accessToken": "a.b.c"})
    transport = FakeTransport(answers={spec_by_id("nsv-token").url: [body]})

    result = await observe(NsvTokenProbe(), transport, SessionState(api_key="warm"))

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)
    assert [request.url for request in transport.requests] == [spec_by_id("nsv-token").url]


async def test_a_cold_session_fetches_the_api_key_first() -> None:
    config_url = spec_by_id("nsv-config").url
    token_url = spec_by_id("nsv-token").url
    transport = FakeTransport(
        answers={
            config_url: [json_response({"arch": {"security": {"apiKey": "fresh"}}})],
            token_url: [json_response({"accessToken": "a.b.c"})],
        }
    )
    session = SessionState()

    result = await observe(NsvTokenProbe(), transport, session)

    assert result.outcome is Outcome.UP
    assert [request.url for request in transport.requests] == [config_url, token_url]
    assert session.api_key == "fresh"
    assert session.access_token == "a.b.c"  # noqa: S105


async def test_a_token_that_is_not_a_jwt_is_a_bad_shape() -> None:
    body = json_response({"accessToken": "nope"})
    result = await observe(
        NsvTokenProbe(),
        FakeTransport(answers={spec_by_id("nsv-token").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)


async def test_stations_accept_a_non_empty_list() -> None:
    body = json_response({"stations": [{"id": 1}]})
    result = await observe(
        NsvStationsProbe(),
        FakeTransport(answers={spec_by_id("nsv-stations").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)


async def test_stations_empty_list_is_degraded() -> None:
    body = json_response({"stations": []})
    result = await observe(
        NsvStationsProbe(),
        FakeTransport(answers={spec_by_id("nsv-stations").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.EMPTY)


async def test_search_wants_a_200_and_nothing_more() -> None:
    body = json_response({"journeys": []})
    result = await observe(
        NsvSearchProbe(),
        FakeTransport(answers={spec_by_id("nsv-search").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)


async def test_an_unexpected_client_error_is_unknown_not_an_outage() -> None:
    result = await observe(
        NsvSearchProbe(),
        FakeTransport(answers={spec_by_id("nsv-search").url: [response(400)]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.UNKNOWN, Reason.PROBE_ERROR)


async def test_the_classic_shop_needs_both_answers() -> None:
    transport = FakeTransport(answers=answers())

    result = await observe(LegacyShopProbe(), transport, WARM)

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)
    assert len(transport.requests) == 2


async def test_the_classic_shop_reports_a_failing_second_call() -> None:
    table = answers(dwr=response(500))
    result = await observe(LegacyShopProbe(), FakeTransport(answers=table), WARM)

    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)


async def test_the_live_map_with_units_is_up() -> None:
    body = json_response({"flota": [{"id": 1}]})
    result = await observe(
        LiveMapProbe(madrid_hour=lambda: 10),
        FakeTransport(answers={spec_by_id("live-map").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)


async def test_an_empty_live_map_in_the_day_is_degraded() -> None:
    body = json_response({"flota": []})
    result = await observe(
        LiveMapProbe(madrid_hour=lambda: 10),
        FakeTransport(answers={spec_by_id("live-map").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.DEGRADED, Reason.EMPTY)


async def test_an_empty_live_map_at_night_is_normal() -> None:
    body = json_response({"flota": []})
    result = await observe(
        LiveMapProbe(madrid_hour=lambda: 4),
        FakeTransport(answers={spec_by_id("live-map").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)


async def test_gtfs_accepts_a_304_and_keeps_the_validator() -> None:
    session = SessionState()
    transport = FakeTransport(
        answers={spec_by_id("gtfs-avld").url: [response(304, headers={"etag": "abc"})]}
    )

    result = await observe(GtfsAvldProbe(), transport, session)

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)
    assert session.gtfs_etag == "abc"


async def test_gtfs_sends_the_validator_it_already_has() -> None:
    transport = FakeTransport(
        answers={spec_by_id("gtfs-avld").url: [response(304)]}
    )

    await observe(GtfsAvldProbe(), transport, SessionState(gtfs_etag="stored"))

    assert transport.requests[0].headers["if-none-match"] == "stored"


async def test_gtfs_rejects_html_instead_of_the_archive() -> None:
    body = response(200, body=b"<html>error</html>")
    result = await observe(
        GtfsAvldProbe(),
        FakeTransport(answers={spec_by_id("gtfs-avld").url: [body]}),
        WARM,
    )

    assert (result.outcome, result.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)


async def test_the_renfe_search_page_needs_its_marker() -> None:
    good = response(200, body=b"<html>buscador de billetes</html>")
    bad = response(200, body=b"<html>mantenimiento</html>")

    up = await observe(
        WwwSearchProbe(),
        FakeTransport(answers={spec_by_id("www-search").url: [good]}),
        WARM,
    )
    down = await observe(
        WwwSearchProbe(),
        FakeTransport(answers={spec_by_id("www-search").url: [bad]}),
        WARM,
    )

    assert (up.outcome, up.reason) == (Outcome.UP, Reason.OK)
    assert (down.outcome, down.reason) == (Outcome.DOWN, Reason.BAD_SHAPE)


async def test_the_control_probe_accepts_a_204() -> None:
    transport = FakeTransport(answers={CONTROL_ENDPOINT.url: [response(204)]})

    result = await ControlProbe().run(
        ProbeContext(
            spec=CONTROL_ENDPOINT,
            http=transport,
            clock=FixedClock(),
            session=SessionState(),
        )
    )

    assert (result.outcome, result.reason) == (Outcome.UP, Reason.OK)


async def test_a_probe_that_raises_is_never_an_outage() -> None:
    class Exploding:
        probe_id = "nsv-config"

        async def send(self, _request: HttpRequest) -> HttpResponse:
            message = "boom"
            raise RuntimeError(message)

    result = await NsvConfigProbe().run(
        ProbeContext(
            spec=spec_by_id("nsv-config"),
            http=Exploding(),
            clock=FixedClock(),
            session=SessionState(),
        )
    )

    assert (result.outcome, result.reason) == (Outcome.UNKNOWN, Reason.PROBE_ERROR)


@pytest.mark.parametrize("blocked_status", [403, 429])
async def test_a_blocked_status_is_never_an_outage(blocked_status: int) -> None:
    result = await observe(
        NsvConfigProbe(),
        FakeTransport(answers={spec_by_id("nsv-config").url: [response(blocked_status)]}),
        WARM,
    )

    assert result.outcome is Outcome.BLOCKED
    assert result.counts_in_denominator() is False
