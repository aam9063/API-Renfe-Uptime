"""The only place that reads the environment.

Everything else takes its values as arguments, so tests never depend on the machine they run on.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

URL_VARIABLE = "SUPABASE_URL"
SERVICE_KEY_VARIABLE = "SUPABASE_SERVICE_ROLE_KEY"
REGION_VARIABLE = "ANDEN9_REGION"
DEFAULT_REGION = "es-madrid"


class ConfigError(RuntimeError):
    """The environment is missing something the prober cannot invent."""


@dataclass(frozen=True, slots=True)
class Config:
    """What the prober needs to run, and nothing about how it measures."""

    supabase_url: str
    service_role_key: str
    region: str = DEFAULT_REGION

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] | None = None) -> Config:
        source = os.environ if environ is None else environ
        url = source.get(URL_VARIABLE, "").strip()
        key = source.get(SERVICE_KEY_VARIABLE, "").strip()
        if not url or not key:
            missing = [
                name
                for name, value in ((URL_VARIABLE, url), (SERVICE_KEY_VARIABLE, key))
                if not value
            ]
            message = f"missing environment: {', '.join(missing)}"
            raise ConfigError(message)
        region = source.get(REGION_VARIABLE, "").strip() or DEFAULT_REGION
        return cls(supabase_url=url.rstrip("/"), service_role_key=key, region=region)

    def __repr__(self) -> str:
        """Never let the service key reach a log line or a traceback."""
        return f"Config(supabase_url={self.supabase_url!r}, region={self.region!r})"
