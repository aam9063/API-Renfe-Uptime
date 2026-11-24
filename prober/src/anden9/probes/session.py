"""State one probe learns and another reuses, without globals."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(slots=True)
class SessionState:
    """The anonymous session of the new shop and the validator of the GTFS archive.

    Probes fill it as they observe it, so `nsv-token` reuses the API key that `nsv-config` found
    instead of asking for it twice, and `gtfs-avld` sends the `ETag` of the last archive it saw.
    """

    api_key: str | None = None
    session_id: str = field(default_factory=lambda: str(uuid4()))
    terminal_id: str | None = None
    access_token: str | None = None
    gtfs_etag: str | None = None
