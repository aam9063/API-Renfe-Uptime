"""The scheduler writing to the store: checks, incidents, heartbeat, and a database that fails."""

from __future__ import annotations

import io
import json
from collections.abc import Sequence
from contextlib import redirect_stderr
from datetime import UTC, datetime

from anden9.domain.outcome import CheckResult, Outcome, Reason
from anden9.domain.ports import HttpResponse
from anden9.domain.spec import ProbeSpec
from anden9.domain.store import CheckRecord, IncidentRecord
from anden9.probes.catalog import CONTROL_ENDPOINT, dev_catalog, spec_by_id
from anden9.scheduler import Scheduler
from fakes import FakeTransport, FixedClock, json_response, response

LIVE_MAP = spec_by_id("live-map")
WWW_SEARCH = spec_by_id("www-search")
MAP_UNITS = json_response({"flota": [{"id": 1}]})
SEARCH_PAGE = response(200, body=b"<html>buscador de billetes</html>")


class RecordingStore:
    """A store that remembers everything and can be told to fail."""

    def __init__(self, *, failing: bool = False) -> None:
        self.calls: list[tuple[str, object]] = []
        self.failing = failing

    async def upsert_probes(self, specs: Sequence[ProbeSpec]) -> None:
        self.calls.append(("upsert_probes", len(specs)))

    async def record_check(self, record: CheckRecord) -> None:
        if self.failing:
            message = "database is down"
            raise RuntimeError(message)
        self.calls.append(("record_check", record.result.outcome))

    async def open_incident(self, record: IncidentRecord) -> None:
        self.calls.append(("open_incident", record.kind))

    async def close_incident(self, probe_id: str, ended_at: datetime) -> None:
        self.calls.append(("close_incident", probe_id))

    async def beat_heartbeat(
        self,
        *,
        region: str,
        probe_version: str,
        at: datetime,
    ) -> None:
        self.calls.append(("beat_heartbeat", region))


def transport(*, map_answers: list[HttpResponse] | None = None) -> FakeTransport:
    return FakeTransport(
        answers={
            LIVE_MAP.url: list(map_answers or [MAP_UNITS]),
            WWW_SEARCH.url: [SEARCH_PAGE],
            CONTROL_ENDPOINT.url: [response(204)],
        }
    )


def build(http: FakeTransport, store: RecordingStore) -> Scheduler:
    return Scheduler(
        http=http,
        clock=FixedClock(moment=datetime(2026, 1, 1, 12, 0, tzinfo=UTC)),
        specs=dev_catalog(),
        store=store,
    )


async def test_the_catalog_is_upserted_once_and_the_heartbeat_beats_every_tick() -> None:
    store = RecordingStore()
    engine = build(transport(), store)

    await engine.tick(0)
    await engine.tick(60)

    kinds = [name for name, _ in store.calls]
    assert kinds.count("upsert_probes") == 1
    assert kinds.count("beat_heartbeat") == 2
    assert kinds.count("record_check") == 3


async def test_two_failures_open_an_incident_and_two_successes_close_it() -> None:
    store = RecordingStore()
    engine = build(
        transport(
            map_answers=[
                response(503),
                response(503),
                MAP_UNITS,
                MAP_UNITS,
                MAP_UNITS,
            ]
        ),
        store,
    )

    await engine.tick(0)
    await engine.tick(60)
    await engine.tick(120)
    await engine.tick(180)

    opened = [value for name, value in store.calls if name == "open_incident"]
    closed = [value for name, value in store.calls if name == "close_incident"]
    assert opened == [Outcome.DOWN]
    assert closed == ["live-map"]


async def test_a_database_failure_does_not_kill_the_loop() -> None:
    store = RecordingStore(failing=True)
    engine = build(transport(), store)
    stderr = io.StringIO()

    with redirect_stderr(stderr):
        observed = await engine.tick(0)

    assert len(observed) == 2
    assert all(result.outcome is Outcome.UP for _, result in observed)
    line = json.loads(stderr.getvalue().strip().splitlines()[0])
    assert line["event"] == "store_failed"
    assert line["probe"] == "live-map"


async def test_without_a_store_the_loop_still_measures() -> None:
    engine = Scheduler(
        http=transport(),
        clock=FixedClock(),
        specs=dev_catalog(),
    )

    observed = await engine.tick(0)

    assert [result.outcome for _, result in observed] == [Outcome.UP, Outcome.UP]


async def test_a_blocked_probe_is_written_and_opens_no_incident() -> None:
    store = RecordingStore()
    engine = build(transport(map_answers=[response(403)]), store)

    await engine.tick(0)
    await engine.tick(60)
    await engine.tick(120)

    written = [value for name, value in store.calls if name == "record_check"]
    assert written.count(Outcome.BLOCKED) == 3
    assert [value for name, value in store.calls if name == "open_incident"] == [Outcome.BLOCKED]


async def test_the_control_probe_gates_a_down_before_it_reaches_the_store() -> None:
    store = RecordingStore()
    http = transport(map_answers=[response(503)])
    http.answers[CONTROL_ENDPOINT.url] = [response(500)]
    engine = build(http, store)

    await engine.tick(0)

    written = [value for name, value in store.calls if name == "record_check"]
    assert Outcome.DOWN not in written


def test_the_seeded_probe_ids_are_the_ones_the_views_expect() -> None:
    ids = {spec.probe_id for spec in dev_catalog()}

    assert ids == {"live-map", "www-search"}
    assert CheckResult(Outcome.UP, Reason.OK, 200, 10).counts_as_available()
