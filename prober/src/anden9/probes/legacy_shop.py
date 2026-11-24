"""Classic shop: the search page plus the DWR call that opens the session.

The minimal sequence is uncertainty 4 of the brief, so this probe measures transport-level
availability only: two answers with a 200 on the same host. It deliberately does not fail on the
content of the DWR response until the sequence has been confirmed by observation, because a wrong
body of ours must not become an outage of Renfe.
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
SEARCH_PAGE_PATH = "/vol/buscarTren.do?Idioma=es&Pais=ES"
DWR_PATH = "/vol/dwr/call/plaincall/__System.generateId.dwr"
DWR_BODY = (
    "callCount=1"
    "&c0-scriptName=__System"
    "&c0-methodName=generateId"
    "&c0-id=0"
    "&batchId=0"
    "&page=%2Fvol%2FbuscarTren.do"
    "&httpSessionId="
    "&scriptSessionId="
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
            first = await context.http.send(page)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)

        return classify(first, context.spec, payload=read_payload(first))

    async def _session_call(
        self,
        context: ProbeContext,
        classified: CheckResult,
    ) -> CheckResult:
        dwr = HttpRequest(
            method="POST",
            url=f"{_origin(context.spec.url)}{DWR_PATH}",
            timeout_s=context.spec.timeout_s,
            headers={
                "accept": "text/plain",
                "content-type": "text/plain",
                "origin": _origin(context.spec.url),
                "referer": context.spec.url,
            },
            body=DWR_BODY.encode("utf-8"),
        )
        try:
            second = await context.http.send(dwr)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        if second.status != EXPECTED_STATUS:
            return CheckResult(Outcome.DOWN, Reason.BAD_SHAPE, second.status, second.elapsed_ms)
        return classified
