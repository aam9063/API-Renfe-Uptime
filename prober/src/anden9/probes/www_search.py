"""The ticket search page of renfe.com, the one a person opens in a browser."""

from __future__ import annotations

from dataclasses import dataclass

from anden9.domain.classifier import (
    PayloadState,
    classify,
    classify_failure,
    classify_probe_error,
)
from anden9.domain.outcome import CheckResult
from anden9.domain.ports import HttpError, HttpRequest, HttpResponse
from anden9.probes.base import ProbeContext

PROBE_ID = "www-search"
EXPECTED_STATUS = 200
PAGE_MARKERS = (b"buscador", b"billetes")


def read_payload(response: HttpResponse) -> PayloadState:
    """A 200 with the search page itself, never a bare or empty document."""
    if response.status != EXPECTED_STATUS:
        return PayloadState.INVALID
    lowered = response.body.lower()
    if any(marker in lowered for marker in PAGE_MARKERS):
        return PayloadState.VALID
    return PayloadState.INVALID


@dataclass(frozen=True, slots=True)
class WwwSearchProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        request = HttpRequest(
            method="GET",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
            headers={"accept": "text/html"},
        )
        try:
            response = await context.http.send(request)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        return classify(response, context.spec, payload=read_payload(response))
