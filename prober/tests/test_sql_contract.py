"""The shared contract cases, run against the SQL that the views use.

This is the second implementation of the formula: if it ever disagrees with
`prober/src/anden9/domain/uptime.py`, one of them is wrong and the page would publish it.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import httpx
import pytest

from local_db import ANON_KEY, LOCAL_URL, SERVICE_KEY, headers, requires_local_db

pytestmark = [pytest.mark.integration, requires_local_db]

CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "uptime_cases.json"
TOLERANCE = 1e-12


def as_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"expected an integer, got {value!r}"
        raise TypeError(message)
    return value


def cases() -> list[dict[str, object]]:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    raw = payload["cases"]
    assert isinstance(raw, list)
    return [case for case in raw if isinstance(case, dict)]


def summarise(seconds: dict[str, int], window_seconds: int) -> dict[str, object]:
    response = httpx.post(
        f"{LOCAL_URL}/rest/v1/rpc/uptime_summary",
        headers=headers(SERVICE_KEY),
        json={
            "p_up": seconds["up"],
            "p_degraded": seconds["degraded"],
            "p_down": seconds["down"],
            "p_blocked": seconds["blocked"],
            "p_unknown": seconds["unknown"],
            "p_window_seconds": window_seconds,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    rows = response.json()
    assert isinstance(rows, list)
    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row, dict)
    return row


@pytest.mark.parametrize("case", cases(), ids=[str(case["name"]) for case in cases()])
def test_contract_case_matches_the_sql(case: dict[str, object]) -> None:
    seconds = case["seconds"]
    expect = case["expect"]
    assert isinstance(seconds, dict)
    assert isinstance(expect, dict)

    row = summarise(
        {key: as_int(value) for key, value in seconds.items()},
        as_int(case["window_seconds"]),
    )

    assert row["available_seconds"] == expect["available_seconds"]
    assert row["denominator_seconds"] == expect["denominator_seconds"]
    assert row["down_seconds"] == expect["down_seconds"]
    assert row["nines"] == expect["nines"]
    assert row["insufficient"] is expect["insufficient"]
    assert row["display_percent"] == expect["display_percent"]
    assert row["no_downtime"] is (expect["label"] == "sin caídas")

    expected_uptime = expect["uptime"]
    got_uptime = row["uptime"]
    if expected_uptime is None:
        assert got_uptime is None
    else:
        assert isinstance(got_uptime, (int, float))
        expected = float(Fraction(str(expected_uptime)))
        assert abs(float(got_uptime) - expected) < TOLERANCE


def test_a_window_with_no_checks_has_no_denominator() -> None:
    row = summarise({"up": 0, "degraded": 0, "down": 0, "blocked": 0, "unknown": 0}, 86400)

    assert row["denominator_seconds"] == 0
    assert row["uptime"] is None
    assert row["display_percent"] is None
    assert row["insufficient"] is True


def test_the_anon_key_can_call_the_formula_too() -> None:
    response = httpx.post(
        f"{LOCAL_URL}/rest/v1/rpc/uptime_summary",
        headers=headers(ANON_KEY),
        json={
            "p_up": 86400,
            "p_degraded": 0,
            "p_down": 0,
            "p_blocked": 0,
            "p_unknown": 0,
            "p_window_seconds": 86400,
        },
        timeout=15.0,
    )

    assert response.status_code == 200
