"""Incident state machine of one probe: two failures of a kind open, two successes close.

Rules, pinned by tests:

- ``down``, ``degraded`` and ``blocked`` are separate kinds. Two consecutive checks of the
  same kind open an incident of that kind; its start is the first of those two checks.
- Two consecutive ``up`` checks close the open incident; it ends at the first of those two.
- While an incident is open, two consecutive checks of another failing kind close it and
  open a new one of that kind, both at the first check of the new streak.
- ``unknown`` says nothing about Renfe: it neither opens, closes nor breaks a streak.
- At most one incident is open per probe.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime

from anden9.domain.outcome import Outcome

OPEN_AFTER = 2
CLOSE_AFTER = 2
INCIDENT_KINDS = frozenset({Outcome.DOWN, Outcome.DEGRADED, Outcome.BLOCKED})


@dataclass(frozen=True, slots=True)
class Streak:
    """Consecutive checks with the same outcome, ignoring ``unknown``."""

    outcome: Outcome
    first_at: datetime
    count: int


@dataclass(frozen=True, slots=True)
class OpenIncident:
    kind: Outcome
    started_at: datetime
    checks_count: int


@dataclass(frozen=True, slots=True)
class TrackerState:
    streak: Streak | None = None
    open: OpenIncident | None = None


@dataclass(frozen=True, slots=True)
class IncidentOpened:
    kind: Outcome
    started_at: datetime
    checks_count: int


@dataclass(frozen=True, slots=True)
class IncidentExtended:
    kind: Outcome
    started_at: datetime
    checks_count: int


@dataclass(frozen=True, slots=True)
class IncidentClosed:
    kind: Outcome
    started_at: datetime
    ended_at: datetime
    checks_count: int


IncidentEvent = IncidentOpened | IncidentExtended | IncidentClosed


def _extend(streak: Streak | None, outcome: Outcome, at: datetime) -> Streak:
    if streak is not None and streak.outcome is outcome:
        return replace(streak, count=streak.count + 1)
    return Streak(outcome=outcome, first_at=at, count=1)


def _opened(streak: Streak) -> tuple[OpenIncident, IncidentOpened]:
    incident = OpenIncident(streak.outcome, streak.first_at, streak.count)
    return incident, IncidentOpened(incident.kind, incident.started_at, incident.checks_count)


def _closed(incident: OpenIncident, ended_at: datetime) -> IncidentClosed:
    return IncidentClosed(incident.kind, incident.started_at, ended_at, incident.checks_count)


def step(
    state: TrackerState, outcome: Outcome, at: datetime
) -> tuple[TrackerState, tuple[IncidentEvent, ...]]:
    """Feed one check, in chronological order, and return the new state and its events."""
    if outcome is Outcome.UNKNOWN:
        return state, ()

    streak = _extend(state.streak, outcome, at)
    incident = state.open

    if incident is None:
        if outcome in INCIDENT_KINDS and streak.count >= OPEN_AFTER:
            opened, event = _opened(streak)
            return TrackerState(streak, opened), (event,)
        return TrackerState(streak, None), ()

    if outcome is incident.kind:
        extended = replace(incident, checks_count=incident.checks_count + 1)
        event_ext = IncidentExtended(extended.kind, extended.started_at, extended.checks_count)
        return TrackerState(streak, extended), (event_ext,)

    if outcome is Outcome.UP and streak.count >= CLOSE_AFTER:
        return TrackerState(streak, None), (_closed(incident, streak.first_at),)

    if outcome in INCIDENT_KINDS and streak.count >= OPEN_AFTER:
        opened, event = _opened(streak)
        return TrackerState(streak, opened), (_closed(incident, streak.first_at), event)

    return TrackerState(streak, incident), ()


def replay(
    checks: Iterable[tuple[Outcome, datetime]], state: TrackerState | None = None
) -> tuple[TrackerState, tuple[IncidentEvent, ...]]:
    """Rebuild the state from stored checks, so a restart never forgets an open streak."""
    current = state or TrackerState()
    events: list[IncidentEvent] = []
    for outcome, at in checks:
        current, produced = step(current, outcome, at)
        events.extend(produced)
    return current, tuple(events)
