"""The contract every probe implements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from anden9.domain.outcome import CheckResult
from anden9.domain.ports import Clock, HttpPort
from anden9.domain.spec import ProbeSpec


@dataclass(frozen=True, slots=True)
class ProbeContext:
    """Everything a probe may use, injected so a test can replace it."""

    spec: ProbeSpec
    http: HttpPort
    clock: Clock


@runtime_checkable
class Probe(Protocol):
    """One endpoint, one request, one classified result."""

    probe_id: str

    async def run(self, context: ProbeContext) -> CheckResult: ...
