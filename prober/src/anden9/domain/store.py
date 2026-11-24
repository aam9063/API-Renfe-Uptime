"""The store port: the only way a measurement leaves the prober."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from anden9.domain.outcome import CheckResult, Outcome
from anden9.domain.spec import ProbeSpec


@dataclass(frozen=True, slots=True)
class CheckRecord:
    """One stored check, with the two facts the probe does not own."""

    spec: ProbeSpec
    result: CheckResult
    region: str
    probe_version: str
    started_at: datetime


@dataclass(frozen=True, slots=True)
class IncidentRecord:
    """One incident, as the state machine of the domain described it."""

    probe_id: str
    kind: Outcome
    started_at: datetime
    ended_at: datetime | None
    checks_count: int
    region: str


class Store(Protocol):
    """Writes. Reads belong to the views, never to the prober."""

    async def upsert_probes(self, specs: Sequence[ProbeSpec]) -> None: ...

    async def record_check(self, record: CheckRecord) -> None: ...

    async def open_incident(self, record: IncidentRecord) -> None: ...

    async def close_incident(self, probe_id: str, ended_at: datetime) -> None: ...

    async def beat_heartbeat(self, *, region: str, probe_version: str, at: datetime) -> None: ...
