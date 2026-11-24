"""Interval coverage: what each check owns, and what is honestly a gap."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from anden9.domain.coverage import ObservedCheck, SecondShares, cover
from anden9.domain.outcome import Outcome

START = datetime(2026, 1, 1, tzinfo=UTC)
INTERVAL_S = 60


def at(seconds: int) -> datetime:
    return START + timedelta(seconds=seconds)


def test_every_second_of_a_fully_covered_window_belongs_to_a_state() -> None:
    checks = [ObservedCheck(at(index * INTERVAL_S), Outcome.UP) for index in range(10)]
    shares = cover(
        checks,
        interval_s=INTERVAL_S,
        window_start=START,
        window_end=at(10 * INTERVAL_S),
    )

    assert shares.total == 10 * INTERVAL_S
    assert shares.of(Outcome.UP) == 10 * INTERVAL_S
    assert shares.of(Outcome.UNKNOWN) == 0


def test_the_space_after_the_last_check_is_a_gap() -> None:
    checks = [ObservedCheck(at(0), Outcome.UP), ObservedCheck(at(60), Outcome.UP)]
    shares = cover(checks, interval_s=INTERVAL_S, window_start=START, window_end=at(300))

    assert shares.of(Outcome.UP) == 180
    assert shares.of(Outcome.UNKNOWN) == 120


def test_a_check_covers_at_most_twice_its_interval() -> None:
    checks = [ObservedCheck(at(0), Outcome.DOWN)]
    shares = cover(checks, interval_s=INTERVAL_S, window_start=START, window_end=at(600))

    assert shares.of(Outcome.DOWN) == 120
    assert shares.of(Outcome.UNKNOWN) == 480


def test_a_check_never_covers_over_the_next_one() -> None:
    checks = [ObservedCheck(at(0), Outcome.DOWN), ObservedCheck(at(30), Outcome.UP)]
    shares = cover(checks, interval_s=INTERVAL_S, window_start=START, window_end=at(60))

    assert shares.of(Outcome.DOWN) == 30
    assert shares.of(Outcome.UP) == 30
    assert shares.of(Outcome.UNKNOWN) == 0


def test_a_check_before_the_window_still_covers_its_first_seconds() -> None:
    checks = [ObservedCheck(at(-30), Outcome.DOWN), ObservedCheck(at(60), Outcome.UP)]
    shares = cover(checks, interval_s=INTERVAL_S, window_start=START, window_end=at(120))

    assert shares.of(Outcome.DOWN) == 60
    assert shares.of(Outcome.UP) == 60
    assert shares.of(Outcome.UNKNOWN) == 0


def test_a_window_without_checks_is_entirely_unknown() -> None:
    shares = cover([], interval_s=INTERVAL_S, window_start=START, window_end=at(300))

    assert shares.total == 300
    assert shares.of(Outcome.UNKNOWN) == 300


def test_an_inverted_window_covers_nothing() -> None:
    shares = cover([], interval_s=INTERVAL_S, window_start=at(60), window_end=START)

    assert shares.total == 0


def test_shares_ignore_empty_and_negative_additions() -> None:
    shares = SecondShares()
    shares.add(Outcome.UP, 0)
    shares.add(Outcome.UP, -5)
    shares.add(Outcome.UP, 7)

    assert shares.of(Outcome.UP) == 7
    assert shares.total == 7
