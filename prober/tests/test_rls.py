"""The row level security promise, checked against the local database.

`anon` reads the public views and nothing else. If this test ever fails, the page could leak the raw
checks or, worse, someone could write a measurement.
"""

from __future__ import annotations

import httpx
import pytest

from local_db import ANON_KEY, LOCAL_URL, SERVICE_KEY, headers, requires_local_db

pytestmark = [pytest.mark.integration, requires_local_db]

TABLES = ("checks", "incidents", "probes", "heartbeat", "daily_rollups")
VIEWS = (
    "v_status_now",
    "v_uptime_windows",
    "v_daily_90",
    "v_latency_24h",
    "v_recent_checks",
    "v_incidents",
    "v_probes",
    "v_heartbeat",
)


@pytest.mark.parametrize("table", TABLES)
def test_anon_cannot_read_a_raw_table(table: str) -> None:
    response = httpx.get(
        f"{LOCAL_URL}/rest/v1/{table}",
        headers=headers(ANON_KEY),
        params={"select": "*", "limit": "1"},
        timeout=15.0,
    )

    assert response.status_code in {401, 403, 404}, response.text


WRITE_ATTEMPTS: dict[str, dict[str, object]] = {
    "probes": {
        "id": "intruder",
        "name": "intruder",
        "group_name": "web",
        "host": "example.test",
        "method": "GET",
        "url_display": "/",
        "interval_s": 60,
        "timeout_s": 10,
        "degraded_ms": 1000,
    },
    "checks": {
        "probe_id": "live-map",
        "started_at": "2026-01-01T00:00:00Z",
        "duration_ms": 1,
        "outcome": "up",
        "reason": "ok",
        "region": "test",
        "probe_version": "0.1.0",
    },
    "incidents": {
        "probe_id": "live-map",
        "kind": "down",
        "started_at": "2026-01-01T00:00:00Z",
        "checks_count": 2,
    },
    "heartbeat": {
        "region": "intruder",
        "last_seen": "2026-01-01T00:00:00Z",
        "probe_version": "0",
    },
    "daily_rollups": {"probe_id": "live-map", "day": "2026-01-01", "up_seconds": 0},
}


@pytest.mark.parametrize("table", TABLES)
def test_anon_cannot_write_a_table(table: str) -> None:
    """A well-formed row, so the answer is a permission and not a validation error."""
    response = httpx.post(
        f"{LOCAL_URL}/rest/v1/{table}",
        headers=headers(ANON_KEY),
        json=[WRITE_ATTEMPTS[table]],
        timeout=15.0,
    )

    assert response.status_code >= 400, response.text

def test_anon_wrote_nothing() -> None:
    """Read the two rows that would exist if a write had gone through."""
    probes = httpx.get(
        f"{LOCAL_URL}/rest/v1/probes",
        headers=headers(SERVICE_KEY),
        params={"select": "id", "id": "eq.intruder"},
        timeout=15.0,
    ).json()
    regions = httpx.get(
        f"{LOCAL_URL}/rest/v1/heartbeat",
        headers=headers(SERVICE_KEY),
        params={"select": "region", "region": "eq.intruder"},
        timeout=15.0,
    ).json()

    assert probes == []
    assert regions == []
