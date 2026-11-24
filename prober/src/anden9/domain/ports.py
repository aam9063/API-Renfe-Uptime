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


RETRY_AFTER_HEADER = "retry-after"
MAX_RETRY_AFTER_S = 3600


def retry_after_seconds(headers: Mapping[str, str]) -> int | None:
    """`Retry-After` in whole seconds, capped at an hour, or `None` when absent or unreadable."""
    raw = header_value(headers, RETRY_AFTER_HEADER)
    if raw is None or not raw.isdigit():
        return None
    return min(int(raw), MAX_RETRY_AFTER_S)


def header_value(headers: Mapping[str, str], name: str) -> str | None:
    for header_name, value in headers.items():
        if header_name.lower() == name:
            return value.strip()
    return None


class Clock(Protocol):
    """The only place time comes from; faked in tests."""

    def now(self) -> datetime: ...
