"""Ports implemented by the adapters, so tests run with no network and no clock."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from anden9.domain.outcome import Reason


@dataclass(frozen=True, slots=True)
class HttpRequest:
    """One outbound request, with its own timeout and no retry policy."""

    method: str
    url: str
    timeout_s: float
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes | None = None


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """A response that arrived, whatever its status code."""

    status: int
    headers: Mapping[str, str]
    body: bytes
    elapsed_ms: int
    received_at: datetime


class HttpError(Exception):
    """A request that never produced a response: timeout, DNS, TLS or a refused socket."""

    def __init__(self, reason: Reason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class HttpPort(Protocol):
    """One in-flight request per host, honest identity, no retries."""

    async def send(self, request: HttpRequest) -> HttpResponse: ...


class Clock(Protocol):
    """The only place time comes from; faked in tests."""

    def now(self) -> datetime: ...
