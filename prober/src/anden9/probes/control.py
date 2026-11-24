"""Neutral endpoint that proves the network works, so a failure is never blamed on Renfe."""

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

PROBE_ID = "control"
EXPECTED_STATUS = 204


def read_payload(response: HttpResponse) -> PayloadState:
    return PayloadState.VALID if response.status == EXPECTED_STATUS else PayloadState.INVALID


@dataclass(frozen=True, slots=True)
class ControlProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        request = HttpRequest(
            method="GET",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
        )
        try:
            response = await context.http.send(request)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        return classify(response, context.spec, payload=read_payload(response))
