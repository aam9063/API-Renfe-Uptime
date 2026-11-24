"""The single place where the measured endpoints and their rhythm are declared."""

from __future__ import annotations

from collections.abc import Sequence

from anden9.domain.budget import BudgetEntry
from anden9.domain.spec import ProbeSpec

CONTROL_ENDPOINT = ProbeSpec(
    probe_id="control",
    module="control",
    name="Control endpoint",
    group="control",
    host="www.google.com",
    method="GET",
    url="https://www.google.com/generate_204",
    interval_s=300,
    timeout_s=10.0,
    degraded_ms=3000,
)

CATALOG: tuple[ProbeSpec, ...] = (
    ProbeSpec(
        probe_id="nsv-config",
        module="nsv_config",
        name="Web configuration",
        group="venta nueva",
        host="venta.rsv.renfe.com",
        method="GET",
        url="https://venta.rsv.renfe.com/config/arch-config.json",
        interval_s=300,
        timeout_s=10.0,
        degraded_ms=3000,
    ),
    ProbeSpec(
        probe_id="nsv-token",
        module="nsv_token",
        name="Public token",
        group="venta nueva",
        host="api.rsv.renfe.com",
        method="GET",
        url="https://api.rsv.renfe.com/user/external-users-login/v1/tokens/public",
        interval_s=300,
        timeout_s=10.0,
        degraded_ms=3000,
    ),
    ProbeSpec(
        probe_id="nsv-stations",
        module="nsv_stations",
        name="Station catalog",
        group="venta nueva",
        host="api.rsv.renfe.com",
        method="GET",
        url="https://api.rsv.renfe.com/catalog/masterdata/v1/stations",
        interval_s=900,
        timeout_s=10.0,
        degraded_ms=3000,
        heavy=True,
    ),
    ProbeSpec(
        probe_id="nsv-search",
        module="nsv_search",
        name="Journey search",
        group="venta nueva",
        host="api.rsv.renfe.com",
        method="POST",
        url="https://api.rsv.renfe.com/browsing/traveloptions/v1/search-travel",
        interval_s=900,
        timeout_s=15.0,
        degraded_ms=5000,
        heavy=True,
    ),
    ProbeSpec(
        probe_id="legacy-shop",
        module="legacy_shop",
        name="Classic ticket shop",
        group="venta clásica",
        host="venta.renfe.com",
        method="GET",
        url="https://venta.renfe.com/vol/buscarTren.do?Idioma=es&Pais=ES",
        interval_s=900,
        timeout_s=15.0,
        degraded_ms=6000,
        heavy=True,
        requests_per_run=2,
    ),
    ProbeSpec(
        probe_id="live-map",
        module="live_map",
        name="Live long distance map",
        group="información",
        host="tiempo-real.largorecorrido.renfe.com",
        method="GET",
        url="https://tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json",
        interval_s=60,
        timeout_s=10.0,
        degraded_ms=2000,
    ),
    ProbeSpec(
        probe_id="gtfs-avld",
        module="gtfs_avld",
        name="AV and LD schedules",
        group="información",
        host="ssl.renfe.com",
        method="GET",
        url="https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip",
        interval_s=900,
        timeout_s=20.0,
        degraded_ms=5000,
        heavy=True,
    ),
    ProbeSpec(
        probe_id="www-search",
        module="www_search",
        name="renfe.com ticket search",
        group="web",
        host="www.renfe.com",
        method="GET",
        url="https://www.renfe.com/es/es/buscador-billetes",
        interval_s=300,
        timeout_s=10.0,
        degraded_ms=3000,
    ),
)

DEV_CATALOG_IDS = ("live-map", "www-search")


def spec_by_id(probe_id: str) -> ProbeSpec:
    for spec in CATALOG:
        if spec.probe_id == probe_id:
            return spec
    message = f"unknown probe: {probe_id}"
    raise KeyError(message)


def dev_catalog() -> tuple[ProbeSpec, ...]:
    """The reduced catalog of the local stack: one fast probe and one cheap HTML probe."""
    return tuple(spec for spec in CATALOG if spec.probe_id in DEV_CATALOG_IDS)


def budget_entries(specs: Sequence[ProbeSpec] = CATALOG) -> tuple[BudgetEntry, ...]:
    return tuple(
        BudgetEntry(
            probe_id=spec.probe_id,
            interval_s=spec.interval_s,
            requests_per_run=spec.requests_per_run,
            heavy=spec.heavy,
        )
        for spec in specs
    )
