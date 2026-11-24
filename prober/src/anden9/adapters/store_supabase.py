"""Supabase store over PostgREST.

No client library: the three writes the prober needs are one HTTP call each, and the transport is
already a dependency. The service role key is read from `config.py` and never logged.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

import httpx

from anden9.domain.spec import ProbeSpec
from anden9.domain.store import CheckRecord, IncidentRecord


def _iso(moment: datetime) -> str:
    return moment.isoformat()


class SupabaseStore:
    """Writes checks, incidents and the heartbeat with the service role key."""

    def __init__(
        self,
        *,
        url: str,
        service_role_key: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base = f"{url.rstrip('/')}/rest/v1"
        self._headers = {
            "apikey": service_role_key,
            "authorization": f"Bearer {service_role_key}",
            "content-type": "application/json",
        }
        self._client = client or httpx.AsyncClient(timeout=15.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _post(self, table: str, payload: object, *, prefer: str) -> None:
        response = await self._client.post(
            f"{self._base}/{table}",
            headers={**self._headers, "prefer": prefer},
            json=payload,
        )
        response.raise_for_status()

    async def _patch(self, table: str, filters: Mapping[str, str], payload: object) -> None:
        response = await self._client.patch(
            f"{self._base}/{table}",
            headers={**self._headers, "prefer": "return=minimal"},
            params=dict(filters),
            json=payload,
        )
        response.raise_for_status()

    async def upsert_probes(self, specs: Sequence[ProbeSpec]) -> None:
        payload = [
            {
                "id": spec.probe_id,
                "name": spec.name,
                "group_name": spec.group,
                "host": spec.host,
                "method": spec.method,
                "url_display": spec.url,
                "interval_s": spec.interval_s,
                "timeout_s": spec.timeout_s,
                "degraded_ms": spec.degraded_ms,
                "enabled": True,
                "retired_at": spec.retired_at,
                "sort": index * 10,
            }
            for index, spec in enumerate(specs, start=1)
        ]
        await self._post("probes", payload, prefer="resolution=merge-duplicates,return=minimal")

    async def record_check(self, record: CheckRecord) -> None:
        await self._post(
            "checks",
            [
                {
                    "probe_id": record.spec.probe_id,
                    "started_at": _iso(record.started_at),
                    "duration_ms": record.result.duration_ms,
                    "http_status": record.result.http_status,
                    "outcome": record.result.outcome.value,
                    "reason": record.result.reason.value,
                    "region": record.region,
                    "probe_version": record.probe_version,
                }
            ],
            prefer="return=minimal",
        )

    async def open_incident(self, record: IncidentRecord) -> None:
        await self._post(
            "incidents",
            [
                {
                    "probe_id": record.probe_id,
                    "kind": record.kind.value,
                    "started_at": _iso(record.started_at),
                    "ended_at": None,
                    "checks_count": record.checks_count,
                }
            ],
            prefer="return=minimal",
        )

    async def close_incident(self, probe_id: str, ended_at: datetime) -> None:
        await self._patch(
            "incidents",
            {"probe_id": f"eq.{probe_id}", "ended_at": "is.null"},
            {"ended_at": _iso(ended_at)},
        )

    async def beat_heartbeat(self, *, region: str, probe_version: str, at: datetime) -> None:
        await self._post(
            "heartbeat",
            [{"region": region, "last_seen": _iso(at), "probe_version": probe_version}],
            prefer="resolution=merge-duplicates,return=minimal",
        )
