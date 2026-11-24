"""Live long distance map, probed every minute because its outages are short."""

from __future__ import annotations

import json
from collections.abc import Callable
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

PROBE_ID = "live-map"
EXPECTED_STATUS = 200
FIRST_ACTIVE_HOUR = 7
LAST_ACTIVE_HOUR = 23


def has_content(body: object) -> bool:
    """The map is a JSON object whose value is a list of units, possibly empty."""
    if isinstance(body, list):
        return bool(body)
    if isinstance(body, dict):
        return any(isinstance(value, list) and value for value in body.values())
    return False


def read_payload(response: HttpResponse, *, madrid_hour: int) -> PayloadState:
    """An empty map is normal at night and degraded while the service should be running."""
    if response.status != EXPECTED_STATUS:
        return PayloadState.INVALID
    try:
        body = json.loads(response.body)
    except ValueError:
        return PayloadState.INVALID
    if not isinstance(body, dict):  # noqa: SIM102
        if not isinstance(body, list):
            return PayloadState.INVALID
    if has_content(body):
        return PayloadState.VALID
    active = FIRST_ACTIVE_HOUR <= madrid_hour < LAST_ACTIVE_HOUR
    return PayloadState.EMPTY if active else PayloadState.VALID


@dataclass(frozen=True, slots=True)
class LiveMapProbe:
    probe_id: str = PROBE_ID
    madrid_hour: Callable[[], int] | None = None

    def _hour(self, context: ProbeContext) -> int:
        if self.madrid_hour is not None:
            return self.madrid_hour()
        return context.clock.now().hour

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
        payload = read_payload(response, madrid_hour=self._hour(context))
        return classify(response, context.spec, payload=payload)
