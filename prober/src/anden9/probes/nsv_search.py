"""Journey search of the new shop: one fixed route, one fixed date.

The body is the part of this probe that is still unconfirmed (uncertainty 3 of the brief). WHAT:
on 2026-11-24 the endpoint answered 401 with only the API key, so it also sends the anonymous
Bearer token that `nsv-token` already fetched. An unexpected 4xx becomes `unknown` in the
classifier, never a published outage, so a wrong body can cost us a measurement but can never
invent a failure of Renfe.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta

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

PROBE_ID = "nsv-search"
EXPECTED_STATUS = 200
MIN_SALE_DATE = date(2027, 1, 26)
LEAD_DAYS = 90
ORIGIN_CODE = "MAD"
DESTINATION_CODE = "BCN"


def search_date(today: date) -> date:
    """A date the new shop can sell, at least ninety days ahead."""
    candidate = today + timedelta(days=LEAD_DAYS)
    return max(candidate, MIN_SALE_DATE)


def search_body(today: date) -> bytes:
    """Documented as unconfirmed in `docs/probes.md`: the shape is easy to fix, the route is not."""
    payload = {
        "origin": ORIGIN_CODE,
        "destination": DESTINATION_CODE,
        "departureDate": search_date(today).isoformat(),
        "passengers": [{"type": "ADULT", "quantity": 1}],
    }
    return json.dumps(payload).encode("utf-8")


def read_payload(response: HttpResponse) -> PayloadState:
    """A 200 answers the search, even when that date happens to have no trains."""
    return PayloadState.VALID if response.status == EXPECTED_STATUS else PayloadState.INVALID


@dataclass(frozen=True, slots=True)
class NsvSearchProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        await api_key(context, context.session)
        headers = session_headers(context.session)
        headers["content-type"] = "application/json"
        if context.session.access_token is not None:
            headers["authorization"] = f"Bearer {context.session.access_token}"
        request = HttpRequest(
            method="POST",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
            headers=headers,
            body=search_body(context.clock.now().date()),
        )
        try:
            response = await context.http.send(request)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        return classify(response, context.spec, payload=read_payload(response))
