"""The opt-in health endpoint, for platforms that only keep HTTP containers alive."""

from __future__ import annotations

import httpx
import pytest

from anden9.adapters.health import start_health_server
from anden9.config import Config, ConfigError


def test_it_answers_ok_on_the_health_path() -> None:
    server = start_health_server(0)
    port = server.server_address[1]
    try:
        response = httpx.get(f"http://127.0.0.1:{port}/healthz", timeout=5.0)
    finally:
        server.shutdown()
        server.server_close()

    assert response.status_code == 200
    assert response.text == "ok\n"


def test_it_is_not_a_second_api() -> None:
    server = start_health_server(0)
    port = server.server_address[1]
    try:
        response = httpx.get(f"http://127.0.0.1:{port}/checks", timeout=5.0)
    finally:
        server.shutdown()
        server.server_close()

    assert response.status_code == 404


def test_the_port_is_optional_and_validated() -> None:
    base = {
        "SUPABASE_URL": "https://project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "key",
    }

    assert Config.from_environ(base).health_port is None
    assert Config.from_environ({**base, "ANDEN9_HEALTH_PORT": "3000"}).health_port == 3000
    with pytest.raises(ConfigError, match="ANDEN9_HEALTH_PORT"):
        Config.from_environ({**base, "ANDEN9_HEALTH_PORT": "nope"})
