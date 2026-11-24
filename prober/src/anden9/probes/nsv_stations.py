"""Station catalog of the new shop: a non-empty list is the whole proof."""

from __future__ import annotations

import json
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
from anden9.probes.nsv_headers import session_headers
from anden9.probes.nsv_token import api_key

PROBE_ID = "nsv-stations"
EXPECTED_STATUS = 200
LIST_KEYS = ("stations", "data", "items")


def _lists(body: object) -> list[object] | None:
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for key in LIST_KEYS:
            candidate = body.get(key)
            if isinstance(candidate, list):
                return candidate
    return None


def read_payload(response: HttpResponse) -> PayloadState:
    """A 200 with a non-empty list of stations."""
    if response.status != EXPECTED_STATUS:
        return PayloadState.INVALID
    try:
        body = json.loads(response.body)
    except ValueError:
        return PayloadState.INVALID
    stations = _lists(body)
    if stations is None:
        return PayloadState.INVALID
    if not stations:
        return PayloadState.EMPTY
    return PayloadState.VALID


@dataclass(frozen=True, slots=True)
class NsvStationsProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        await api_key(context, context.session)
        request = HttpRequest(
            method="GET",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
            headers=session_headers(context.session),
        )
        try:
            response = await context.http.send(request)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        return classify(response, context.spec, payload=read_payload(response))
