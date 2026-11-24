"""Shared settings for the tests that need the local Supabase stack.

They are skipped unless the two keys are exported, so `pytest` stays green on a machine without
Docker. Get them with `npx supabase status` and export them for one command:

    ANDEN9_LOCAL_ANON_KEY=... ANDEN9_LOCAL_SERVICE_KEY=... uv run pytest -m integration
"""

from __future__ import annotations

import os

import pytest

LOCAL_URL = os.environ.get("ANDEN9_LOCAL_URL", "http://127.0.0.1:54321")
ANON_KEY = os.environ.get("ANDEN9_LOCAL_ANON_KEY", "")
SERVICE_KEY = os.environ.get("ANDEN9_LOCAL_SERVICE_KEY", "")

requires_local_db = pytest.mark.skipif(
    not (ANON_KEY and SERVICE_KEY),
    reason="export ANDEN9_LOCAL_ANON_KEY and ANDEN9_LOCAL_SERVICE_KEY to run the database tests",
)


def headers(key: str) -> dict[str, str]:
    return {"apikey": key, "authorization": f"Bearer {key}"}
