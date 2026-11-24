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
def test_anon_cannot_read_a_raw_table(table: str) -> None:
    response = httpx.get(
        f"{LOCAL_URL}/rest/v1/{table}",
        headers=headers(ANON_KEY),
        params={"select": "*", "limit": "1"},
        timeout=15.0,
    )

    assert response.status_code in {401, 403, 404}, response.text


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


@pytest.mark.parametrize("view", VIEWS)
def test_anon_can_read_every_public_view(view: str) -> None:
    """Not just a 200: the two views that call a function must actually return rows.

    A view declared `security_invoker = false` runs as its owner, but a plain SQL function it calls
    still runs as `anon`, and that answers 401 with "permission denied for table checks". The row
    count is what catches it.
    """
    response = httpx.get(
        f"{LOCAL_URL}/rest/v1/{view}",
        headers=headers(ANON_KEY),
        params={"select": "*", "limit": "1"},
        timeout=15.0,
    )

    assert response.status_code == 200, response.text
    rows = response.json()
    assert isinstance(rows, list)


@pytest.mark.parametrize("view", ["v_uptime_windows", "v_daily_90"])
def test_the_views_backed_by_a_function_return_rows_for_anon(view: str) -> None:
    response = httpx.get(
        f"{LOCAL_URL}/rest/v1/{view}",
        headers=headers(ANON_KEY),
        params={"select": "*", "limit": "5"},
        timeout=15.0,
    )

    assert response.status_code == 200, response.text
    assert len(response.json()) > 0


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


def test_the_seeded_views_answer_the_numbers_the_page_needs() -> None:
    windows = httpx.get(
        f"{LOCAL_URL}/rest/v1/v_uptime_windows",
        headers=headers(ANON_KEY),
        params={"select": "probe_id,window_key,display_percent,nines", "limit": "40"},
        timeout=15.0,
    ).json()
    now = httpx.get(
        f"{LOCAL_URL}/rest/v1/v_status_now",
        headers=headers(ANON_KEY),
        params={"select": "probe_id,outcome,reason"},
        timeout=15.0,
    ).json()

    assert len(windows) == 32
    assert {row["window_key"] for row in windows} == {"24h", "7d", "30d", "90d"}
    assert len(now) == 8
    assert all(row["outcome"] in {"up", "degraded", "down", "blocked", "unknown"} for row in now)
