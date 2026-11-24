"""AV and LD schedules: a conditional GET, so a 304 costs almost nothing."""

from __future__ import annotations

from dataclasses import dataclass

from anden9.domain.classifier import (
    PayloadState,
    classify,
    classify_failure,
    classify_probe_error,
)
from anden9.domain.outcome import CheckResult
from anden9.domain.ports import HttpError, HttpRequest, HttpResponse, header_value
from anden9.probes.base import ProbeContext

PROBE_ID = "gtfs-avld"
NOT_MODIFIED = 304
OK = 200
ZIP_MAGIC = b"PK"
ETAG_HEADER = "etag"


def read_payload(response: HttpResponse) -> PayloadState:
    """A 304 is the archive being unchanged; a 200 must be the zip, not an HTML error page."""
    if response.status == NOT_MODIFIED:
        return PayloadState.VALID
    if response.status != OK:
        return PayloadState.INVALID
    if not response.body.startswith(ZIP_MAGIC):
        return PayloadState.INVALID
    return PayloadState.VALID


@dataclass(frozen=True, slots=True)
class GtfsAvldProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        headers = {"accept": "*/*"}
        if context.session.gtfs_etag is not None:
            headers["if-none-match"] = context.session.gtfs_etag
        request = HttpRequest(
            method="GET",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
            headers=headers,
        )
        try:
            response = await context.http.send(request)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        etag = header_value(response.headers, ETAG_HEADER)
        if etag is not None:
            context.session.gtfs_etag = etag
        return classify(response, context.spec, payload=read_payload(response))
