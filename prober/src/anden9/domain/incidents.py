"""Incident state machine of one probe: two failures of a kind open, two successes close.

Rules, pinned by tests:

- `down`, `degraded` and `blocked` are separate kinds. Two consecutive checks of the same kind open
  an incident of that kind, and its start is the first of those two checks.
- Two consecutive `up` checks close the open incident, at the first of those two.
- While an incident is open, two consecutive checks of another failing kind close it and open a new
  one of that kind, both at the first check of the new streak.
- `unknown` says nothing about Renfe: it neither opens, closes nor breaks a streak.
- At most one incident is open per probe.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from anden9.domain.outcome import Outcome

FAILING_KINDS = frozenset({Outcome.DOWN, Outcome.DEGRADED, Outcome.BLOCKED})
OPEN_AFTER = 2
CLOSE_AFTER = 2


@dataclass(frozen=True, slots=True)
class Incident:
    kind: Outcome
    started_at: datetime
    checks_count: int
    ended_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.ended_at is None

    @property
    def duration_s(self) -> int | None:
        if self.ended_at is None:
            return None
        return int((self.ended_at - self.started_at).total_seconds())


@dataclass(frozen=True, slots=True)
class Opened:
    incident: Incident


@dataclass(frozen=True, slots=True)
class Closed:
    incident: Incident


IncidentEvent = Opened | Closed


@dataclass(frozen=True, slots=True)
class IncidentState:
    opened: Incident | None = None
    streak_outcome: Outcome | None = None
    streak_started_at: datetime | None = None
    streak_length: int = 0


EMPTY_STATE = IncidentState()


def advance(
    state: IncidentState,
    *,
    outcome: Outcome,
    at: datetime,
) -> tuple[IncidentState, tuple[IncidentEvent, ...]]:
    """Feed one check into the machine and get the new state with what happened."""
    if outcome is Outcome.UNKNOWN:
        return state, ()

    if outcome is state.streak_outcome:
        streak_length = state.streak_length + 1
        streak_started_at = state.streak_started_at or at
    else:
        streak_length = 1
        streak_started_at = at

    events: list[IncidentEvent] = []
    opened = state.opened
    just_opened: Incident | None = None

    if opened is None:
        if outcome in FAILING_KINDS and streak_length == OPEN_AFTER:
            opened = Incident(outcome, streak_started_at, OPEN_AFTER)
            just_opened = opened
            events.append(Opened(opened))
    elif outcome is Outcome.UP:
        if streak_length == CLOSE_AFTER:
            closed = replace(opened, ended_at=streak_started_at)
            events.append(Closed(closed))
            opened = None
    elif outcome in FAILING_KINDS and outcome is not opened.kind and streak_length == OPEN_AFTER:
        events.append(Closed(replace(opened, ended_at=streak_started_at)))
        opened = Incident(outcome, streak_started_at, OPEN_AFTER)
        just_opened = opened
        events.append(Opened(opened))

    if opened is not None and just_opened is None:
        opened = replace(opened, checks_count=opened.checks_count + 1)

    return (
        IncidentState(
            opened=opened,
            streak_outcome=outcome,
            streak_started_at=streak_started_at,
            streak_length=streak_length,
        ),
        tuple(events),
    )
