"""The only code that performs HTTP requests.

One request per run, no retry, an honest User-Agent and one in-flight request per host. Transport
errors become a `Reason` the classifier understands, so a refused socket or a broken name never
looks like an outage of Renfe.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from anden9.domain.outcome import Reason
from anden9.domain.ports import HttpError, HttpPort, HttpRequest, HttpResponse
from anden9.version import __version__

SITE_URL = "https://anden9.dev/metodologia"
USER_AGENT = f"anden9-probe/{__version__} (+{SITE_URL})"
DNS_MARKERS = (
    "getaddrinfo",
    "name or service not known",
    "nodename nor servname",
    "temporary failure in name resolution",
)


class HttpxTransport(HttpPort):
    """Async transport with one lock per host."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        user_agent: str = USER_AGENT,
    ) -> None:
        self._user_agent = user_agent
        self._client = client or httpx.AsyncClient(follow_redirects=False)
        self._locks: dict[str, asyncio.Lock] = {}

    async def aclose(self) -> None:
        await self._client.aclose()

    def _lock(self, request: HttpRequest) -> asyncio.Lock:
        host = urlsplit(request.url).netloc
        lock = self._locks.get(host)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[host] = lock
        return lock

    async def send(self, request: HttpRequest) -> HttpResponse:
        async with self._lock(request):
            return await self._send(request)

    async def _send(self, request: HttpRequest) -> HttpResponse:
        headers = {"User-Agent": self._user_agent, **request.headers}
        started_at = time.perf_counter()
        try:
            response = await self._client.request(
                request.method,
                request.url,
                headers=headers,
                content=request.body,
                timeout=request.timeout_s,
            )
        except httpx.TimeoutException as error:
            raise HttpError(Reason.TIMEOUT) from error
        except httpx.ConnectError as error:
            raise HttpError(_connect_reason(error)) from error
        except httpx.HTTPError as error:
            raise HttpError(Reason.CONN_REFUSED) from error
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return HttpResponse(
            status=response.status_code,
            headers=dict(response.headers),
            body=response.content,
            elapsed_ms=elapsed_ms,
            received_at=datetime.now(tz=UTC),
        )


def _connect_reason(error: httpx.ConnectError) -> Reason:
    message = str(error).lower()
    if any(marker in message for marker in DNS_MARKERS):
        return Reason.DNS
    return Reason.CONN_REFUSED
