"""Classic shop: the search page plus the DWR call that opens the session.

The minimal sequence is uncertainty 4 of the brief, so this probe measures transport-level
availability only: two answers with a 200 on the same host. It deliberately does not fail on the
content of the DWR response until the sequence has been confirmed by observation, because a wrong
body of ours must not become an outage of Renfe.

WHAT: the DWR call takes plain text lines, not a query string, and names the page that answered the
search. Read from `renfe-cli` (`src/renfe/legacy.py`) on 2026-11-24.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from anden9.domain.classifier import (
    PayloadState,
    classify,
    classify_failure,
    classify_probe_error,
)
from anden9.domain.outcome import CheckResult, Outcome, Reason
from anden9.domain.ports import HttpError, HttpRequest, HttpResponse
from anden9.probes.base import ProbeContext
from anden9.version import __version__

PROBE_ID = "legacy-shop"
EXPECTED_STATUS = 200
DWR_PATH = "/vol/dwr/call/plaincall/__System.generateId.dwr"
DWR_PAGE = "/vol/buscarTrenEnlaces.do"
DWR_BODY = "\n".join(
    (
        "callCount=1",
        "c0-scriptName=__System",
        "c0-methodName=generateId",
        "c0-id=0",
        "batchId=0",
        "instanceId=0",
        "page=%2Fvol%2FbuscarTrenEnlaces.do",
        "scriptSessionId=",
        "windowName=",
        "",
    )
)


def read_payload(response: HttpResponse) -> PayloadState:
    return PayloadState.VALID if response.status == EXPECTED_STATUS else PayloadState.INVALID


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


@dataclass(frozen=True, slots=True)
class LegacyShopProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        classified = await self._search_page(context)
        if classified.outcome is not Outcome.UP:
            return classified
        return await self._session_call(context, classified)

    async def _search_page(self, context: ProbeContext) -> CheckResult:
        page = HttpRequest(
            method="GET",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
            headers={"accept": "text/html", "user-agent": f"anden9-probe/{__version__}"},
        )
        try:
            response = await context.http.send(page)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        return classify(response, context.spec, payload=read_payload(response))

    async def _session_call(
        self,
        context: ProbeContext,
        classified: CheckResult,
    ) -> CheckResult:
        origin = _origin(context.spec.url)
        dwr = HttpRequest(
            method="POST",
            url=f"{origin}{DWR_PATH}",
            timeout_s=context.spec.timeout_s,
            headers={
                "accept": "*/*",
                "content-type": "text/plain",
                "origin": origin,
                "referer": f"{origin}{DWR_PAGE}",
            },
            body=DWR_BODY.encode("utf-8"),
        )
        try:
            response = await context.http.send(dwr)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        if response.status != EXPECTED_STATUS:
            return CheckResult(Outcome.DOWN, Reason.BAD_SHAPE, response.status, response.elapsed_ms)
        return classified
