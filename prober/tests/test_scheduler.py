"""The scheduler: cadence, control gate and the pause a 429 asks for."""

from __future__ import annotations

import pytest

from anden9.domain.budget import BudgetError
from anden9.domain.outcome import Outcome, Reason
from anden9.domain.ports import HttpResponse
from anden9.probes.catalog import CONTROL_ENDPOINT, dev_catalog, spec_by_id
from anden9.scheduler import Scheduler
from fakes import FakeTransport, FixedClock, json_response, response

LIVE_MAP = spec_by_id("live-map")
WWW_SEARCH = spec_by_id("www-search")
MAP_UNITS = json_response({"flota": [{"id": 1}]})
SEARCH_PAGE = response(200, body=b"<html>buscador de billetes</html>")


def transport(
    map_answer: HttpResponse | None = None,
    search_answer: HttpResponse | None = None,
) -> FakeTransport:
    return FakeTransport(
        answers={
            LIVE_MAP.url: [map_answer if map_answer is not None else MAP_UNITS],
            WWW_SEARCH.url: [search_answer if search_answer is not None else SEARCH_PAGE],
            CONTROL_ENDPOINT.url: [response(204)],
        }
    )


def scheduler(http: FakeTransport, specs: tuple[object, ...] | None = None) -> Scheduler:
    return Scheduler(
        http=http,
        clock=FixedClock(),
        specs=specs or dev_catalog(),  # type: ignore[arg-type]
    )


async def test_the_first_tick_runs_every_probe_in_catalog_order() -> None:
    http = transport()
    observed = await scheduler(http).tick(0)

    assert [spec.probe_id for spec, _ in observed] == ["live-map", "www-search"]
    assert [result.outcome for _, result in observed] == [Outcome.UP, Outcome.UP]


async def test_a_probe_is_not_asked_again_before_its_interval() -> None:
    http = transport()
    engine = scheduler(http)
    await engine.tick(0)

    assert await engine.tick(59) == ()


async def test_the_live_map_comes_back_after_its_minute() -> None:
    http = transport()
    engine = scheduler(http)
    await engine.tick(0)

    observed = await engine.tick(60)

    assert [spec.probe_id for spec, _ in observed] == ["live-map"]


async def test_a_down_against_a_healthy_control_endpoint_counts() -> None:
    http = transport(map_answer=response(503))
    observed = await scheduler(http).tick(0)

    map_result = next(result for spec, result in observed if spec.probe_id == "live-map")
    assert (map_result.outcome, map_result.reason) == (Outcome.DOWN, Reason.HTTP_5XX)


async def test_a_down_when_the_control_endpoint_also_fails_is_unknown() -> None:
    http = transport(map_answer=response(503))
    http.answers[CONTROL_ENDPOINT.url] = [response(500)]

    observed = await scheduler(http).tick(0)

    map_result = next(result for spec, result in observed if spec.probe_id == "live-map")
    assert (map_result.outcome, map_result.reason) == (Outcome.UNKNOWN, Reason.CONTROL_FAILED)


async def test_a_retry_after_pauses_the_probe_and_marks_it_blocked() -> None:
    http = transport(map_answer=response(429, headers={"retry-after": "120"}))
    engine = scheduler(http)

    first = await engine.tick(0)
    map_result = next(result for spec, result in first if spec.probe_id == "live-map")
    assert (map_result.outcome, map_result.retry_after_s) == (Outcome.BLOCKED, 120)

    assert [spec.probe_id for spec, _ in await engine.tick(60)] == []
    assert [spec.probe_id for spec, _ in await engine.tick(120)] == ["live-map"]


async def test_the_pause_is_capped_at_one_hour() -> None:
    http = transport(map_answer=response(429, headers={"retry-after": "99999"}))
    observed = await scheduler(http).tick(0)

    map_result = next(result for spec, result in observed if spec.probe_id == "live-map")
    assert map_result.retry_after_s == 3600


async def test_an_impolite_catalog_is_refused_at_startup() -> None:
    fast = LIVE_MAP.__class__(
        probe_id=LIVE_MAP.probe_id,
        module=LIVE_MAP.module,
        name=LIVE_MAP.name,
        group=LIVE_MAP.group,
        host=LIVE_MAP.host,
        method=LIVE_MAP.method,
        url=LIVE_MAP.url,
        interval_s=30,
        timeout_s=LIVE_MAP.timeout_s,
        degraded_ms=LIVE_MAP.degraded_ms,
    )

    with pytest.raises(BudgetError, match="below the 60s floor"):
        scheduler(transport(), specs=(fast,))


async def test_the_emit_hook_sees_every_check() -> None:
    seen: list[str] = []
    engine = Scheduler(
        http=transport(),
        clock=FixedClock(),
        specs=dev_catalog(),
        emit=lambda spec, _result: seen.append(spec.probe_id),
    )

    await engine.tick(0)

    assert seen == ["live-map", "www-search"]
