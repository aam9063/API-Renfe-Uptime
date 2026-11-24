"""The Supabase store: one HTTP call per write, and the service key never in a payload."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx

from anden9.adapters.store_supabase import SupabaseStore
from anden9.domain.outcome import CheckResult, Outcome, Reason
from anden9.domain.spec import ProbeSpec
from anden9.domain.store import CheckRecord, IncidentRecord

BASE = "https://project.supabase.co/rest/v1"
KEY = "service-role-key-for-tests"
SPEC = ProbeSpec(
    probe_id="live-map",
    module="live_map",
    name="Live map",
    group="información",
    host="example.test",
    method="GET",
    url="https://example.test/flota.json",
    interval_s=60,
    timeout_s=10.0,
    degraded_ms=2000,
)
RESULT = CheckResult(Outcome.DOWN, Reason.HTTP_5XX, 503, 120)
AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def store() -> SupabaseStore:
    return SupabaseStore(url="https://project.supabase.co", service_role_key=KEY)


async def test_a_check_is_one_insert_with_the_service_key() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(f"{BASE}/checks").mock(return_value=httpx.Response(201))
        await store().record_check(
            CheckRecord(
                spec=SPEC,
                result=RESULT,
                region="es-madrid",
                probe_version="0.1.0",
                started_at=AT,
            )
        )

    body = route.calls[0].request
    assert body.headers["apikey"] == KEY
    assert body.headers["authorization"] == f"Bearer {KEY}"
    payload = body.content.decode()
    assert '"outcome":"down"' in payload
    assert '"reason":"http_5xx"' in payload
    assert '"probe_id":"live-map"' in payload


async def test_the_catalogo_is_upserted_not_inserted() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(f"{BASE}/probes").mock(return_value=httpx.Response(201))
        await store().upsert_probes((SPEC,))

    assert "resolution=merge-duplicates" in route.calls[0].request.headers["prefer"]


async def test_a_new_incident_is_inserted_open() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(f"{BASE}/incidents").mock(return_value=httpx.Response(201))
        await store().open_incident(
            IncidentRecord(
                probe_id="live-map",
                kind=Outcome.DOWN,
                started_at=AT,
                ended_at=None,
                checks_count=2,
                region="es-madrid",
            )
        )

    payload = route.calls[0].request.content.decode()
    assert '"ended_at":null' in payload
    assert '"checks_count":2' in payload


async def test_closing_an_incident_only_touches_the_open_one() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.patch(f"{BASE}/incidents").mock(return_value=httpx.Response(204))
        await store().close_incident("live-map", AT)

    url = str(route.calls[0].request.url)
    assert "probe_id=eq.live-map" in url
    assert "ended_at=is.null" in url


async def test_the_heartbeat_is_an_upsert() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(f"{BASE}/heartbeat").mock(return_value=httpx.Response(201))
        await store().beat_heartbeat(region="es-madrid", probe_version="0.1.0", at=AT)

    assert "resolution=merge-duplicates" in route.calls[0].request.headers["prefer"]


async def test_a_rejected_write_raises_instead_of_being_swallowed() -> None:
    with respx.mock:
        respx.post(f"{BASE}/checks").mock(return_value=httpx.Response(401, json={"message": "no"}))
        with pytest.raises(httpx.HTTPStatusError):
            await store().record_check(
                CheckRecord(
                spec=SPEC,
                result=RESULT,
                region="es-madrid",
                probe_version="0.1.0",
                started_at=AT,
            )
            )
