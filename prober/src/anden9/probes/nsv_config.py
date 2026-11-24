"""Web configuration of the new shop: the endpoint that publishes the public API key."""

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

PROBE_ID = "nsv-config"
EXPECTED_STATUS = 200
API_KEY_PATH = ("arch", "security", "apiKey")


def read_payload(response: HttpResponse) -> tuple[PayloadState, str | None]:
    """A 200 with `arch.security.apiKey` as a non-empty string, and the key itself."""
    if response.status != EXPECTED_STATUS:
        return PayloadState.INVALID, None
    try:
        data = json.loads(response.body)
    except ValueError:
        return PayloadState.INVALID, None
    node: object = data
    for key in API_KEY_PATH:
        if not isinstance(node, dict) or key not in node:
            return PayloadState.INVALID, None
        node = node[key]
    if not isinstance(node, str) or not node:
        return PayloadState.INVALID, None
    return PayloadState.VALID, node


@dataclass(frozen=True, slots=True)
class NsvConfigProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        request = HttpRequest(
            method="GET",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
            headers={"accept": "application/json"},
        )
        try:
            response = await context.http.send(request)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        payload, api_key = read_payload(response)
        if api_key is not None:
            context.session.api_key = api_key
        return classify(response, context.spec, payload=payload)
