"""A health endpoint for platforms that only run HTTP services.

The prober is a worker: it measures and writes, and has no inbound port. Some platforms, though,
only keep a container alive if it answers HTTP, so this module offers an opt-in endpoint. Without
`ANDEN9_HEALTH_PORT` nothing is started and the prober behaves exactly as before.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HEALTH_PATH = "/healthz"
OK_BODY = b"ok\n"
ANY_INTERFACE = "0.0.0.0"  # noqa: S104  a container has to listen on its pod interface


class _HealthHandler(BaseHTTPRequestHandler):
    """Answers one path and nothing else, so it never becomes a second API by accident."""

    def do_GET(self) -> None:
        if self.path != HEALTH_PATH:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("content-type", "text/plain")
        self.send_header("content-length", str(len(OK_BODY)))
        self.end_headers()
        self.wfile.write(OK_BODY)

    def log_message(self, *args: object) -> None:
        """Silence: the prober logs its own JSON lines, and a probe of /healthz is not news."""


def start_health_server(port: int) -> ThreadingHTTPServer:
    """Serve `/healthz` on a daemon thread and return the server, so a caller can shut it down."""
    server = ThreadingHTTPServer((ANY_INTERFACE, port), _HealthHandler)
    threading.Thread(target=server.serve_forever, name="health", daemon=True).start()
    return server
