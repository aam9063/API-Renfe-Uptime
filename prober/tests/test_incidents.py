"""The incident state machine: two failures open, two successes close, and nothing else."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from anden9.domain.incidents import EMPTY_STATE, Closed, IncidentState, Opened, advance
from anden9.domain.outcome import Outcome

START = datetime(2026, 1, 1, tzinfo=UTC)
OUTCOMES = st.sampled_from(
    [Outcome.UP, Outcome.DOWN, Outcome.DEGRADED, Outcome.BLOCKED, Outcome.UNKNOWN]
)


def at(minute: int) -> datetime:
    return START + timedelta(minutes=minute)


def feed(outcomes: list[Outcome]) -> tuple[IncidentState, list[object]]:
    state = EMPTY_STATE
    events: list[object] = []
    for minute, outcome in enumerate(outcomes):
        state, produced = advance(state, outcome=outcome, at=at(minute))
        events.extend(produced)
    return state, events


def test_two_failures_open_an_incident_from_the_first_one() -> None:
    state, events = feed([Outcome.UP, Outcome.DOWN, Outcome.DOWN])

    assert len(events) == 1
    opened = events[0]
    assert isinstance(opened, Opened)
    assert opened.incident.kind is Outcome.DOWN
    assert opened.incident.started_at == at(1)
    assert opened.incident.checks_count == 2
    assert state.opened == opened.incident


def test_a_single_failure_opens_nothing() -> None:
    state, events = feed([Outcome.UP, Outcome.DOWN, Outcome.UP, Outcome.DOWN])

    assert events == []
    assert state.opened is None


def test_two_successes_close_at_the_first_of_them() -> None:
    state, events = feed(
        [Outcome.DOWN, Outcome.DOWN, Outcome.DOWN, Outcome.UP, Outcome.UP]
    )

    assert len(events) == 2
    opened, closed = events
    assert isinstance(opened, Opened)
    assert isinstance(closed, Closed)
    assert closed.incident.ended_at == at(3)
    assert closed.incident.duration_s == 180
    assert state.opened is None


def test_a_single_success_does_not_close() -> None:
    state, events = feed([Outcome.DOWN, Outcome.DOWN, Outcome.UP, Outcome.DOWN])

    assert state.opened is not None
    assert [event for event in events if isinstance(event, Closed)] == []


def test_unknown_neither_opens_nor_closes_nor_breaks_a_streak() -> None:
    state, events = feed([Outcome.DOWN, Outcome.UNKNOWN, Outcome.DOWN])

    assert len(events) == 1
    assert isinstance(events[0], Opened)
    assert state.opened is not None
    assert state.opened.kind is Outcome.DOWN


def test_another_kind_closes_and_reopens_at_the_first_check_of_the_new_streak() -> None:
    state, events = feed(
        [Outcome.DOWN, Outcome.DOWN, Outcome.DEGRADED, Outcome.DEGRADED]
    )

    assert [type(event) for event in events] == [Opened, Closed, Opened]
    closed = events[1]
    assert isinstance(closed, Closed)
    assert closed.incident.ended_at == at(2)
    assert state.opened is not None
    assert state.opened.kind is Outcome.DEGRADED
    assert state.opened.started_at == at(2)


def test_every_failing_kind_is_tracked_separately() -> None:
    for kind in (Outcome.DOWN, Outcome.DEGRADED, Outcome.BLOCKED):
        state, _ = feed([kind, kind])
        assert state.opened is not None
        assert state.opened.kind is kind


def test_a_long_outage_counts_its_checks() -> None:
    state, _ = feed([Outcome.DOWN] * 10)

    assert state.opened is not None
    assert state.opened.checks_count == 10
    assert state.opened.is_open
    assert state.opened.duration_s is None


@given(outcomes=st.lists(OUTCOMES, max_size=40))
@settings(max_examples=200, deadline=None)
def test_there_is_never_more_than_one_open_incident(outcomes: list[Outcome]) -> None:
    state = EMPTY_STATE
    open_count = 0
    for minute, outcome in enumerate(outcomes):
        state, events = advance(state, outcome=outcome, at=at(minute))
        for event in events:
            if isinstance(event, Opened):
                assert open_count == 0
                open_count = 1
            else:
                assert isinstance(event, Closed)
                assert open_count == 1
                open_count = 0
        assert open_count == (1 if state.opened is not None else 0)
