"""What a probe measures, how often, and when a response counts as slow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Method = Literal["GET", "POST"]
MS_PER_SECOND = 1000


@dataclass(frozen=True, slots=True)
class ProbeSpec:
    """One catalog entry. Every threshold is data here, never a constant in logic."""

    probe_id: str
    module: str
    name: str
    group: str
    host: str
    method: Method
    url: str
    interval_s: int
    timeout_s: float
    degraded_ms: int
    heavy: bool = False
    requests_per_run: int = 1
    retired_at: str | None = None

    @property
    def timeout_ms(self) -> int:
        return int(self.timeout_s * MS_PER_SECOND)
