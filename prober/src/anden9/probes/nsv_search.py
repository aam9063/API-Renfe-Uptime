"""Journey search of the new shop: one fixed route, one fixed window.

WHAT: the body and the headers are the ones `renfe-cli` sends, read from its source on 2026-11-24
(`src/renfe/search.py`, `src/renfe/client.py`): the two timestamps are Madrid midnight expressed in
UTC with `.000Z`, the route is a `travel_path` of `{"code": ...}` and the direction is `OUTBOUND`.
The station codes are the `_u_i_c_station_code` values of the station catalog, and both cities send
their five letter city code.

The probe still accepts a 200 as the only proof and lets an unexpected 4xx become `unknown`, so a
future change in the body costs a measurement instead of publishing a false outage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

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
from anden9.probes.nsv_token import access_token

PROBE_ID = "nsv-search"
EXPECTED_STATUS = 200
MIN_SALE_DATE = date(2027, 1, 26)
LEAD_DAYS = 90
ORIGIN_CODE = "MADRI"
DESTINATION_CODE = "BARCE"
DIRECTION = "OUTBOUND"
MADRID = ZoneInfo("Europe/Madrid")
WIRE_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"


def search_date(today: date) -> date:
    """A date the new shop can sell, at least ninety days ahead."""
    candidate = today + timedelta(days=LEAD_DAYS)
    return max(candidate, MIN_SALE_DATE)


def utc_window(day: date) -> tuple[str, str]:
    """Madrid midnight to the next Madrid midnight, written in UTC."""
    after = datetime.combine(day, time.min, tzinfo=MADRID).astimezone(UTC)
    before = datetime.combine(day + timedelta(days=1), time.min, tzinfo=MADRID).astimezone(UTC)
    return after.strftime(WIRE_FORMAT), before.strftime(WIRE_FORMAT)


def search_body(today: date) -> bytes:
    after, before = utc_window(search_date(today))
    payload = {
        "depart_after_datetime": after,
        "depart_before_datetime": before,
        "travel_path": [{"code": ORIGIN_CODE}, {"code": DESTINATION_CODE}],
        "direction": DIRECTION,
    }
    return json.dumps(payload).encode("utf-8")


def read_payload(response: HttpResponse) -> PayloadState:
    """A 200 answers the search, even when that date happens to have no trains."""
    return PayloadState.VALID if response.status == EXPECTED_STATUS else PayloadState.INVALID


@dataclass(frozen=True, slots=True)
class NsvSearchProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        token = await access_token(context, context.session)
        headers = session_headers(context.session)
        headers["accept"] = "application/json, text/plain, */*"
        headers["content-type"] = "application/json"
        if token is not None:
            headers["authorization"] = f"Bearer {token}"
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
