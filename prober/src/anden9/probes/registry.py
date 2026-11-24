"""The one place that says which module implements which catalog entry."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from anden9.domain.spec import ProbeSpec
from anden9.probes.base import Probe
from anden9.probes.control import ControlProbe
from anden9.probes.gtfs_avld import GtfsAvldProbe
from anden9.probes.legacy_shop import LegacyShopProbe
from anden9.probes.live_map import LiveMapProbe
from anden9.probes.nsv_config import NsvConfigProbe
from anden9.probes.nsv_search import NsvSearchProbe
from anden9.probes.nsv_stations import NsvStationsProbe
from anden9.probes.nsv_token import NsvTokenProbe
from anden9.probes.www_search import WwwSearchProbe


def all_probes() -> tuple[Probe, ...]:
    return (
        ControlProbe(),
        NsvConfigProbe(),
        NsvTokenProbe(),
        NsvStationsProbe(),
        NsvSearchProbe(),
        LegacyShopProbe(),
        LiveMapProbe(),
        GtfsAvldProbe(),
        WwwSearchProbe(),
    )


def probes_for(specs: Sequence[ProbeSpec]) -> Mapping[str, Probe]:
    """The probes that answer these catalog entries, keyed by probe id."""
    available = {probe.probe_id: probe for probe in all_probes()}
    return {spec.probe_id: available[spec.probe_id] for spec in specs}


def control_probe() -> Probe:
    """A fresh instance: the control call keeps no state between runs."""
    return ControlProbe()
