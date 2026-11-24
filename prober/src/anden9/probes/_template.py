"""Canonical probe. Copy this file to ``probes/<module>.py`` and register it in ``catalog.py``.

A probe does three things and nothing else: build exactly one request from its
catalog entry, decide whether the payload is valid, and hand both to the
classifier. The timeout comes from the catalog, there is no retry, and the probe
never decides an uptime number.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from anden9.domain.classifier import Payload, classify, classify_failure, classify_probe_error
from anden9.domain.outcome import CheckResult
from anden9.domain.ports import HttpError, HttpRequest, HttpResponse
from anden9.probes.base import ProbeContext

PROBE_ID = "template"
EXPECTED_STATUS = 200
REQUIRED_KEY = "arch"


def judge_payload(response: HttpResponse) -> Payload:
    """The template endpoint answers 200 with a JSON object holding ``arch``."""
    if response.status != EXPECTED_STATUS:
        return Payload.INVALID
    try:
        payload = json.loads(response.body)
    except json.JSONDecodeError:
        return Payload.INVALID
    if isinstance(payload, dict) and REQUIRED_KEY in payload:
        return Payload.VALID
    return Payload.INVALID


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
        return classify(response, context.spec, payload=judge_payload(response))
