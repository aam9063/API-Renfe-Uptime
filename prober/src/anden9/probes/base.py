"""The contract every probe implements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from anden9.domain.outcome import CheckResult
from anden9.domain.ports import Clock, HttpPort
from anden9.domain.spec import ProbeSpec
from anden9.probes.session import SessionState


@dataclass(frozen=True, slots=True)
class ProbeContext:
    """Everything a probe may use, injected so a test can replace it."""

    spec: ProbeSpec
    http: HttpPort
    clock: Clock
    session: SessionState


@runtime_checkable
class Probe(Protocol):
    """One endpoint, one request, one classified result."""

    @property
    def probe_id(self) -> str: ...

    async def run(self, context: ProbeContext) -> CheckResult: ...
