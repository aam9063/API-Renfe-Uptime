"""The transport: honest identity, every transport error mapped, one request per host in flight."""

from __future__ import annotations

import asyncio

import httpx
import pytest
import respx

from anden9.adapters.http_httpx import USER_AGENT, HttpxTransport
from anden9.domain.outcome import Reason
from anden9.domain.ports import HttpError, HttpRequest

URL = "https://example.test/resource"


def request() -> HttpRequest:
    return HttpRequest(method="GET", url=URL, timeout_s=1.0)


async def test_it_sends_the_honest_user_agent() -> None:
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(URL).mock(return_value=httpx.Response(200, content=b"{}"))
        transport = HttpxTransport()
        response = await transport.send(request())
        await transport.aclose()

    assert response.status == 200
    assert route.calls[0].request.headers["user-agent"] == USER_AGENT
    assert "mozilla" not in USER_AGENT.lower()


async def test_a_timeout_becomes_a_timeout_reason() -> None:
    with respx.mock:
        respx.get(URL).mock(side_effect=httpx.ConnectTimeout("too slow"))
        transport = HttpxTransport()
        with pytest.raises(HttpError) as raised:
            await transport.send(request())
        await transport.aclose()

    assert raised.value.reason is Reason.TIMEOUT


async def test_a_broken_name_becomes_a_dns_reason() -> None:
    with respx.mock:
        respx.get(URL).mock(
            side_effect=httpx.ConnectError("[Errno -2] Name or service not known")
        )
        transport = HttpxTransport()
        with pytest.raises(HttpError) as raised:
            await transport.send(request())
        await transport.aclose()

    assert raised.value.reason is Reason.DNS


async def test_a_refused_socket_becomes_a_refused_reason() -> None:
    with respx.mock:
        respx.get(URL).mock(side_effect=httpx.ConnectError("Connection refused"))
        transport = HttpxTransport()
        with pytest.raises(HttpError) as raised:
            await transport.send(request())
        await transport.aclose()

    assert raised.value.reason is Reason.CONN_REFUSED


async def test_only_one_request_per_host_is_in_flight() -> None:
    active = 0
    peak = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return httpx.Response(200, content=b"{}")

    with respx.mock:
        respx.get(URL).mock(side_effect=handler)
        transport = HttpxTransport()
        await asyncio.gather(*(transport.send(request()) for _ in range(3)))
        await transport.aclose()

    assert peak == 1


async def test_it_records_the_latency_and_the_headers() -> None:
    with respx.mock:
        respx.get(URL).mock(
            return_value=httpx.Response(429, headers={"Retry-After": "120"}, content=b"")
        )
        transport = HttpxTransport()
        response = await transport.send(request())
        await transport.aclose()

    assert response.status == 429
    assert response.headers["retry-after"] == "120"
    assert response.elapsed_ms >= 0
