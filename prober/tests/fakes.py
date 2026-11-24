"""Shared doubles for the probe and scheduler tests: a transport that answers by URL."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from anden9.domain.ports import HttpRequest, HttpResponse


def response(
    status: int,
    *,
    body: bytes = b"{}",
    elapsed_ms: int = 100,
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    return HttpResponse(
        status=status,
        headers=dict(headers or {}),
        body=body,
        elapsed_ms=elapsed_ms,
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def json_response(payload: Any, *, status: int = 200, elapsed_ms: int = 100) -> HttpResponse:
    return response(
        status,
        body=json.dumps(payload).encode("utf-8"),
        elapsed_ms=elapsed_ms,
        headers={"content-type": "application/json"},
    )


@dataclass
class FakeTransport:
    """Answers by URL. The last response of a URL is reused, so a loop can keep asking."""

    answers: dict[str, list[HttpResponse]]
    requests: list[HttpRequest] = field(default_factory=list)

    async def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        queue = self.answers.get(request.url)
        if not queue:
            message = f"no canned answer for {request.method} {request.url}"
            raise AssertionError(message)
        if len(queue) == 1:
            return queue[0]
        return queue.pop(0)


@dataclass
class FixedClock:
    """A clock that only moves when a test moves it."""

    moment: datetime = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.moment
