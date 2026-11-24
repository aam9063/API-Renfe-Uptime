"""When each probe runs, under the request budget and `Retry-After`.

The loop is deterministic from the outside: `tick(now)` runs whatever is due at that instant and
returns what it observed, so a test drives weeks of cadence without sleeping a second.
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from anden9.domain.budget import validate
from anden9.domain.classifier import apply_control_gate
from anden9.domain.incidents import EMPTY_STATE, Closed, IncidentState, Opened, advance
from anden9.domain.outcome import CheckResult, Outcome
from anden9.domain.ports import Clock, HttpPort
from anden9.domain.spec import ProbeSpec
from anden9.domain.store import CheckRecord, IncidentRecord, Store
from anden9.probes.base import Probe, ProbeContext
from anden9.probes.catalog import CATALOG, CONTROL_ENDPOINT, budget_entries
from anden9.probes.registry import control_probe, probes_for
from anden9.probes.session import SessionState
from anden9.version import __version__

TICK_S = 1.0
CONTROL_INTERVAL_S = CONTROL_ENDPOINT.interval_s
DEFAULT_REGION = "es-madrid"
NEWLINE = chr(10)


@dataclass(slots=True)
class Scheduled:
    """One probe with the two timestamps the loop needs."""

    spec: ProbeSpec
    probe: Probe
    next_due_s: float = 0.0
    paused_until_s: float | None = None


@dataclass(slots=True)
class Scheduler:
    """Runs the due probes, gates their failures and honours a `Retry-After`."""

    http: HttpPort
    clock: Clock
    specs: Sequence[ProbeSpec] = CATALOG
    session: SessionState = field(default_factory=SessionState)
    emit: Callable[[ProbeSpec, CheckResult], None] | None = None
    store: Store | None = None
    region: str = DEFAULT_REGION
    _scheduled: list[Scheduled] = field(default_factory=list, init=False)
    _incidents: dict[str, IncidentState] = field(default_factory=dict, init=False)
    _catalogued: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        validate(budget_entries(self.specs))
        probes = probes_for(self.specs)
        self._scheduled = [
            Scheduled(spec=spec, probe=probes[spec.probe_id]) for spec in self.specs
        ]

    def schedule(self) -> tuple[Scheduled, ...]:
        return tuple(self._scheduled)

    async def tick(self, now_s: float) -> tuple[tuple[ProbeSpec, CheckResult], ...]:
        """Run every probe that is due at `now_s`, in catalog order."""
        observed: list[tuple[ProbeSpec, CheckResult]] = []
        for entry in self._scheduled:
            if entry.next_due_s > now_s:
                continue
            if entry.paused_until_s is not None and entry.paused_until_s > now_s:
                continue
            result = await self._execute(entry)
            observed.append((entry.spec, result))
            self._reschedule(entry, now_s, result)
            if self.emit is not None:
                self.emit(entry.spec, result)
            if self.store is not None:
                await self._persist(entry.spec, result, self.clock.now())
        if self.store is not None:
            await self._catalogue_once()
            await self._beat()
        return tuple(observed)

    async def _catalogue_once(self) -> None:
        store = self.store
        if store is None or self._catalogued:
            return
        await store.upsert_probes(self.specs)
        self._catalogued = True

    async def _beat(self) -> None:
        store = self.store
        if store is None:
            return
        await store.beat_heartbeat(
            region=self.region,
            probe_version=__version__,
            at=self.clock.now(),
        )

    async def _persist(self, spec: ProbeSpec, result: CheckResult, at: datetime) -> None:
        """Write the check and whatever the incident machine decided, and never kill the loop."""
        store = self.store
        if store is None:
            return
        try:
            await store.record_check(
                CheckRecord(
                    spec=spec,
                    result=result,
                    region=self.region,
                    probe_version=__version__,
                    started_at=at,
                )
            )
            state, events = advance(
                self._incidents.get(spec.probe_id, EMPTY_STATE),
                outcome=result.outcome,
                at=at,
            )
            self._incidents[spec.probe_id] = state
            for event in events:
                if isinstance(event, Opened):
                    await store.open_incident(
                        IncidentRecord(
                            probe_id=spec.probe_id,
                            kind=event.incident.kind,
                            started_at=event.incident.started_at,
                            ended_at=None,
                            checks_count=event.incident.checks_count,
                            region=self.region,
                        )
                    )
                elif isinstance(event, Closed) and event.incident.ended_at is not None:
                    await store.close_incident(spec.probe_id, event.incident.ended_at)
        except Exception as error:
            # The page must say "sin datos" instead of the loop dying: the heartbeat stops.
            failure = {
                "event": "store_failed",
                "probe": spec.probe_id,
                "error": type(error).__name__,
            }
            sys.stderr.write(json.dumps(failure) + NEWLINE)

    async def _execute(self, entry: Scheduled) -> CheckResult:
        context = ProbeContext(
            spec=entry.spec,
            http=self.http,
            clock=self.clock,
            session=self.session,
        )
        result = await entry.probe.run(context)
        if result.outcome is not Outcome.DOWN:
            return result
        control = await control_probe().run(
            ProbeContext(
                spec=CONTROL_ENDPOINT,
                http=self.http,
                clock=self.clock,
                session=self.session,
            )
        )
        return apply_control_gate(result, control_ok=control.outcome is Outcome.UP)

    def _reschedule(self, entry: Scheduled, now_s: float, result: CheckResult) -> None:
        next_due = now_s + entry.spec.interval_s
        if result.retry_after_s is not None:
            entry.paused_until_s = now_s + result.retry_after_s
            next_due = max(next_due, entry.paused_until_s)
        entry.next_due_s = next_due

    async def run_forever(self, *, max_ticks: int | None = None) -> None:
        ticks = 0
        loop = asyncio.get_running_loop()
        while max_ticks is None or ticks < max_ticks:
            await self.tick(loop.time())
            ticks += 1
            await asyncio.sleep(TICK_S)
