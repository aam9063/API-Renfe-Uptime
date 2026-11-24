"""Uptime, nines and truncation: the shared contract, plus the properties of the acceptance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from anden9.domain.coverage import SecondShares
from anden9.domain.outcome import Outcome
from anden9.domain.uptime import format_percent, nines, summarise

CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "uptime_cases.json"
STATE_KEYS = {
    "up": Outcome.UP,
    "degraded": Outcome.DEGRADED,
    "down": Outcome.DOWN,
    "blocked": Outcome.BLOCKED,
    "unknown": Outcome.UNKNOWN,
}
SECONDS = st.integers(min_value=0, max_value=10_000_000)


@dataclass(frozen=True, slots=True)
class Case:
    """One contract case, already typed, because the JSON is not."""

    name: str
    window_seconds: int
    seconds: dict[str, int]
    available_seconds: int
    denominator_seconds: int
    down_seconds: int
    uptime: Fraction | None
    display_percent: str | None
    nines: int | None
    insufficient: bool
    label: str | None


def _require_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"expected an integer, got {value!r}"
        raise TypeError(message)
    return value


def _require_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        message = f"expected a string or null, got {value!r}"
        raise TypeError(message)
    return value


def _require_bool(value: object) -> bool:
    if not isinstance(value, bool):
        message = f"expected a boolean, got {value!r}"
        raise TypeError(message)
    return value


def _require_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        message = f"expected an object, got {value!r}"
        raise TypeError(message)
    return value


def _require_list(value: object) -> list[object]:
    if not isinstance(value, list):
        message = f"expected a list, got {value!r}"
        raise TypeError(message)
    return value


def parse_cases() -> list[Case]:
    payload = _require_dict(json.loads(CONTRACT.read_text(encoding="utf-8")))
    cases: list[Case] = []
    for raw in _require_list(payload["cases"]):
        entry = _require_dict(raw)
        seconds = _require_dict(entry["seconds"])
        expect = _require_dict(entry["expect"])
        uptime_text = _require_str(expect["uptime"])
        nines_value = expect["nines"]
        cases.append(
            Case(
                name=str(entry["name"]),
                window_seconds=_require_int(entry["window_seconds"]),
                seconds={key: _require_int(seconds[key]) for key in STATE_KEYS},
                available_seconds=_require_int(expect["available_seconds"]),
                denominator_seconds=_require_int(expect["denominator_seconds"]),
                down_seconds=_require_int(expect["down_seconds"]),
                uptime=Fraction(uptime_text) if uptime_text is not None else None,
                display_percent=_require_str(expect["display_percent"]),
                nines=None if nines_value is None else _require_int(nines_value),
                insufficient=_require_bool(expect["insufficient"]),
                label=_require_str(expect["label"]),
            )
        )
    return cases


CASES = parse_cases()


def shares_of(seconds: dict[str, int]) -> SecondShares:
    shares = SecondShares()
    for key, outcome in STATE_KEYS.items():
        shares.add(outcome, seconds[key])
    return shares


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_contract_case(case: Case) -> None:
    summary = summarise(shares_of(case.seconds), window_seconds=case.window_seconds)

    assert summary.available_seconds == case.available_seconds
    assert summary.denominator_seconds == case.denominator_seconds
    assert summary.down_seconds == case.down_seconds
    assert summary.nines == case.nines
    assert summary.insufficient is case.insufficient
    assert summary.label == case.label
    assert summary.uptime == case.uptime

    if case.uptime is None:
        assert case.display_percent is None
    else:
        assert format_percent(case.uptime) == case.display_percent


@given(up=SECONDS, degraded=SECONDS, down=SECONDS, blocked=SECONDS, unknown=SECONDS)
@settings(max_examples=200, deadline=None)
def test_uptime_never_leaves_the_unit_interval(
    up: int,
    degraded: int,
    down: int,
    blocked: int,
    unknown: int,
) -> None:
    window = up + degraded + down + blocked + unknown
    seconds = {"up": up, "degraded": degraded, "down": down, "blocked": blocked, "unknown": unknown}
    summary = summarise(shares_of(seconds), window_seconds=window)

    if summary.uptime is not None:
        assert 0 <= summary.uptime <= 1


@given(up=SECONDS, degraded=SECONDS, down=SECONDS, blocked=SECONDS, unknown=SECONDS)
@settings(max_examples=200, deadline=None)
def test_blocked_and_unknown_never_lower_uptime(
    up: int,
    degraded: int,
    down: int,
    blocked: int,
    unknown: int,
) -> None:
    plain = summarise(
        shares_of({"up": up, "degraded": degraded, "down": down, "blocked": 0, "unknown": 0}),
        window_seconds=up + degraded + down,
    )
    complemented = {
        "up": up,
        "degraded": degraded,
        "down": down,
        "blocked": blocked,
        "unknown": unknown,
    }
    excluded = summarise(
        shares_of(complemented),
        window_seconds=up + degraded + down + blocked + unknown,
    )

    assert excluded.denominator_seconds == plain.denominator_seconds
    assert excluded.uptime == plain.uptime
    assert excluded.nines == plain.nines


@given(up=SECONDS, down=SECONDS)
@settings(max_examples=200, deadline=None)
def test_nines_are_absent_exactly_when_no_second_was_lost(up: int, down: int) -> None:
    seconds = {"up": up, "degraded": 0, "down": down, "blocked": 0, "unknown": 0}
    summary = summarise(shares_of(seconds), window_seconds=up + down)

    assert (summary.nines is None) is (down == 0)


@given(up=SECONDS, down=SECONDS)
@settings(max_examples=200, deadline=None)
def test_display_never_rounds_up(up: int, down: int) -> None:
    seconds = {"up": up, "degraded": 0, "down": down, "blocked": 0, "unknown": 0}
    summary = summarise(shares_of(seconds), window_seconds=up + down)
    if summary.uptime is None:
        return

    whole, cents = format_percent(summary.uptime).split(",")
    shown = Fraction(int(whole) * 100 + int(cents), 100)
    exact = summary.uptime * 100

    assert shown <= exact
    assert exact - shown < 1


@given(down=SECONDS, denominator=st.integers(min_value=1, max_value=10_000_000))
@settings(max_examples=200, deadline=None)
def test_nines_come_from_the_downtime_ratio(down: int, denominator: int) -> None:
    if down > denominator:
        return
    value = nines(down, denominator)

    if down == 0:
        assert value is None
        return
    assert value is not None
    ratio = Fraction(denominator, down)
    assert Fraction(10**value, 1) <= ratio
    if value < 12:
        assert ratio < Fraction(10 ** (value + 1), 1)
