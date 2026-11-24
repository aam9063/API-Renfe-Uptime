"""Public anonymous token of the new shop, the one every other call needs."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass

from anden9.domain.classifier import (
    PayloadState,
    classify,
    classify_failure,
    classify_probe_error,
)
from anden9.domain.outcome import CheckResult
from anden9.domain.ports import HttpError, HttpRequest, HttpResponse
from anden9.probes.base import ProbeContext
from anden9.probes.catalog import spec_by_id
from anden9.probes.nsv_config import NsvConfigProbe
from anden9.probes.session import SessionState

PROBE_ID = "nsv-token"
CONFIG_PROBE_ID = "nsv-config"
EXPECTED_STATUS = 200
TOKEN_FIELD = "accessToken"  # noqa: S105
CHANNEL = "VLP"
JWT_PARTS = 3
TERMINAL_CLAIM = "custom:terminal_id"


def read_payload(response: HttpResponse) -> tuple[PayloadState, str | None]:
    """A 200 with an `accessToken` shaped like a JWT."""
    if response.status != EXPECTED_STATUS:
        return PayloadState.INVALID, None
    try:
        data = json.loads(response.body)
    except ValueError:
        return PayloadState.INVALID, None
    if not isinstance(data, dict):
        return PayloadState.INVALID, None
    token = data.get(TOKEN_FIELD)
    parts = token.split(".") if isinstance(token, str) else []
    if not all(parts) or len(parts) != JWT_PARTS:
        return PayloadState.INVALID, None
    return PayloadState.VALID, token


def terminal_id_of(token: str) -> str | None:
    """The terminal id rides inside the anonymous token as a claim."""
    parts = token.split(".")
    if len(parts) != JWT_PARTS:
        return None
    payload = parts[1]
    padded = payload + "=" * (-len(payload) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, TypeError):
        return None
    if not isinstance(claims, dict):
        return None
    value = claims.get(TERMINAL_CLAIM)
    return value if isinstance(value, str) and value else None


async def api_key(context: ProbeContext, session: SessionState) -> str | None:
    """Reuse the key `nsv-config` already found; ask for it once when the session is cold."""
    if session.api_key is not None:
        return session.api_key
    cold = ProbeContext(
        spec=spec_by_id(CONFIG_PROBE_ID),
        http=context.http,
        clock=context.clock,
        session=session,
    )
    await NsvConfigProbe().run(cold)
    return session.api_key


async def access_token(context: ProbeContext, session: SessionState) -> str | None:
    """Reuse the token this process already minted; mint one when a probe runs alone."""
    if session.access_token is not None:
        return session.access_token
    warm = ProbeContext(
        spec=spec_by_id(PROBE_ID),
        http=context.http,
        clock=context.clock,
        session=session,
    )
    await NsvTokenProbe().run(warm)
    return session.access_token


@dataclass(frozen=True, slots=True)
class NsvTokenProbe:
    probe_id: str = PROBE_ID

    async def run(self, context: ProbeContext) -> CheckResult:
        key = await api_key(context, context.session)
        if key is None:
            return classify_probe_error(context.spec)
        request = HttpRequest(
            method="GET",
            url=context.spec.url,
            timeout_s=context.spec.timeout_s,
            headers={"x-api-key": key, "channel": CHANNEL, "accept": "application/json"},
        )
        try:
            response = await context.http.send(request)
        except HttpError as error:
            return classify_failure(error, context.spec)
        except Exception:
            return classify_probe_error(context.spec)
        payload, token = read_payload(response)
        if token is not None:
            context.session.access_token = token
            terminal_id = terminal_id_of(token)
            if terminal_id is not None:
                context.session.terminal_id = terminal_id
        return classify(response, context.spec, payload=payload)
