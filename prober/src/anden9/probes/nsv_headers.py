"""Anonymous session headers of the new shop, shared by the catalog probes."""

from __future__ import annotations

from anden9.probes.session import SessionState

ORIGIN = "https://venta.rsv.renfe.com"
REFERER = "https://venta.rsv.renfe.com/"
CHANNEL = "VLP"


def session_headers(session: SessionState) -> dict[str, str]:
    """What the anonymous calls send, and nothing that identifies the client as a browser."""
    headers = {
        "accept": "application/json",
        "channel": CHANNEL,
        "origin": ORIGIN,
        "referer": REFERER,
    }
    if session.api_key is not None:
        headers["x-api-key"] = session.api_key
    if session.session_id is not None:
        headers["session-id"] = session.session_id
    if session.terminal_id is not None:
        headers["x-terminal-id"] = session.terminal_id
    return headers
