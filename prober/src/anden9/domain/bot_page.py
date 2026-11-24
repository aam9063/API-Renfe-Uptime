"""Recognises protection pages and waiting rooms, which mean ``blocked`` and never ``down``.

Only markers that a legitimate Renfe page cannot contain are listed: vendor resource paths
and vendor product names of bot protection and virtual queues. Plain words such as
"captcha" or "sala de espera" are excluded on purpose, because station pages talk about
real waiting rooms and login forms may embed a captcha widget.
"""

from __future__ import annotations

from collections.abc import Mapping

from anden9.domain.ports import HttpResponse

SCAN_BYTES = 32_768
HTML_CONTENT_TYPE = "text/html"

MARKERS: tuple[str, ...] = (
    "queue-it",
    "_incapsula_resource",
    "incapsula incident id",
    "/cdn-cgi/challenge-platform",
    "cf-chl-",
    "pardon our interruption",
    "errors.edgesuite.net",
    "/_sec/cp_challenge",
    "captcha-delivery",
    "sala de espera virtual",
)


def header(headers: Mapping[str, str], name: str) -> str:
    """Case-insensitive header lookup; adapters lower-case names but tests may not."""
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return ""


def looks_like_html(response: HttpResponse) -> bool:
    if HTML_CONTENT_TYPE in header(response.headers, "content-type").lower():
        return True
    return response.body[:SCAN_BYTES].lstrip().startswith(b"<")


def is_bot_page(response: HttpResponse) -> bool:
    """True when the body is an HTML page served by a bot protection or a virtual queue."""
    if not looks_like_html(response):
        return False
    head = response.body[:SCAN_BYTES].decode("utf-8", errors="replace").lower()
    return any(marker in head for marker in MARKERS)
