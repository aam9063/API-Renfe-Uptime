"""Canonical probe. Copy this file to ``probes/<module>.py`` and register it in ``catalog.py``.

A probe does three things and nothing else: build exactly one request from its catalog entry, say
whether the payload is valid, empty or invalid, and hand that to the classifier. The timeout comes
from the catalog, there is no retry, and the probe never decides an uptime number.
"""

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

PROBE_ID = "template"
EXPECTED_STATUS = 200
REQUIRED_KEY = "arch"


def read_payload(response: HttpResponse) -> PayloadState:
    """The template endpoint answers 200 with a JSON object holding ``arch``."""
    if response.status != EXPECTED_STATUS:
        return PayloadState.INVALID
    try:
        payload = json.loads(response.body)
    except json.JSONDecodeError:
        return PayloadState.INVALID
    if not isinstance(payload, dict) or REQUIRED_KEY not in payload:
        return PayloadState.INVALID
    return PayloadState.VALID


@dataclass(frozen=True, slots=True)
class TemplateProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        request = HttpRequest(
            method=context.spec.method,
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
