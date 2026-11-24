"""The catalog is data, so its shape is worth pinning: ids, modules, thresholds."""

from __future__ import annotations

from anden9.domain.budget import MIN_HEAVY_INTERVAL_S, MIN_INTERVAL_S
from anden9.probes import _template
from anden9.probes.catalog import CATALOG, CONTROL_ENDPOINT, dev_catalog, spec_by_id


def test_every_probe_has_a_unique_id_and_a_module_name() -> None:
    ids = [spec.probe_id for spec in CATALOG]
    assert len(ids) == len(set(ids))
    for spec in CATALOG:
        assert spec.module == spec.probe_id.replace("-", "_")


def test_the_brief_catalog_is_complete() -> None:
    assert {spec.probe_id for spec in CATALOG} == {
        "nsv-config",
        "nsv-token",
        "nsv-stations",
        "nsv-search",
        "legacy-shop",
        "live-map",
        "gtfs-avld",
        "www-search",
    }


def test_heavy_probes_are_the_four_of_the_rules() -> None:
    heavy = {spec.probe_id for spec in CATALOG if spec.heavy}
    assert heavy == {"nsv-stations", "nsv-search", "legacy-shop", "gtfs-avld"}
    for spec in CATALOG:
        floor = MIN_HEAVY_INTERVAL_S if spec.heavy else MIN_INTERVAL_S
        assert spec.interval_s >= floor, spec.probe_id


def test_classic_shop_costs_two_requests_and_the_rest_one() -> None:
    for spec in CATALOG:
        expected = 2 if spec.probe_id == "legacy-shop" else 1
        assert spec.requests_per_run == expected


def test_degraded_threshold_is_reachable_before_the_timeout() -> None:
    for spec in CATALOG:
        assert spec.degraded_ms < spec.timeout_ms, spec.probe_id


def test_the_template_is_not_a_measured_endpoint() -> None:
    assert _template.PROBE_ID not in {spec.probe_id for spec in CATALOG}


def test_lookup_and_dev_catalog() -> None:
    assert spec_by_id("control") is CONTROL_ENDPOINT
    assert spec_by_id("live-map").host == "tiempo-real.largorecorrido.renfe.com"
    assert [spec.probe_id for spec in dev_catalog()] == ["live-map", "www-search"]
    assert CONTROL_ENDPOINT.probe_id == "control"
