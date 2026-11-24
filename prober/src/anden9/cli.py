"""Command line entry point: one-shot checks, the scheduler and a log reader.

`probe once` never writes to a database: it is the level-2 verification of the brief, the one a
person runs against the real Renfe at most once every five minutes and never in a loop.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence

from anden9.adapters.clock import SystemClock
from anden9.adapters.health import start_health_server
from anden9.adapters.http_httpx import HttpxTransport
from anden9.adapters.store_supabase import SupabaseStore
from anden9.config import Config, ConfigError
from anden9.domain.classifier import apply_control_gate
from anden9.domain.outcome import CheckResult, Outcome
from anden9.domain.spec import ProbeSpec
from anden9.domain.store import Store
from anden9.probes.base import Probe, ProbeContext
from anden9.probes.catalog import CATALOG, CONTROL_ENDPOINT, dev_catalog, spec_by_id
from anden9.probes.registry import control_probe, probes_for
from anden9.probes.session import SessionState
from anden9.scheduler import DEFAULT_REGION, Scheduler
from anden9.version import __version__

EXIT_OK = 0
EXIT_USAGE = 2
NEWLINE = chr(10)
LOG_PREFIX = "  "


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="anden9", description="Unofficial Renfe API prober")
    parser.add_argument("--version", action="version", version=f"anden9-probe/{__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    probe = commands.add_parser("probe", help="run one probe and print what it saw")
    probe_commands = probe.add_subparsers(dest="probe_command", required=True)
    once = probe_commands.add_parser("once", help="one shot, no database writes")
    once.add_argument("probe_id", nargs="?", help="catalog id, for example live-map")
    once.add_argument("--all", action="store_true", help="every probe of the catalog")
    once.add_argument("--verbose", action="store_true", help="also print the request line")

    run = commands.add_parser("run", help="run the scheduler until stopped")
    run.add_argument(
        "--catalog",
        choices=("dev", "full"),
        default="dev",
        help="dev is the reduced catalog of the local stack",
    )

    commands.add_parser("logs", help="pretty print the JSON lines on standard input")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "logs":
        return tail_logs()
    if args.command == "probe":
        return asyncio.run(_probe_once(args))
    specs = dev_catalog() if args.catalog == "dev" else CATALOG
    return asyncio.run(_run_scheduler(specs))


async def _probe_once(args: argparse.Namespace) -> int:
    probe_id: str | None = args.probe_id
    if probe_id is None and not args.all:
        sys.stdout.write("choose a probe id or --all\n")
        return EXIT_USAGE
    specs: tuple[ProbeSpec, ...] = (
        (spec_by_id(probe_id),) if probe_id is not None else CATALOG
    )

    transport = HttpxTransport()
    clock = SystemClock()
    session = SessionState()
    probes = probes_for(specs)
    try:
        for spec in specs:
            result = await _observe(probes[spec.probe_id], spec, transport, clock, session)
            write_result(spec, result, verbose=bool(args.verbose))
    finally:
        await transport.aclose()
    return EXIT_OK


async def _observe(
    probe: Probe,
    spec: ProbeSpec,
    transport: HttpxTransport,
    clock: SystemClock,
    session: SessionState,
) -> CheckResult:
    result = await probe.run(
        ProbeContext(spec=spec, http=transport, clock=clock, session=session)
    )
    if result.outcome is not Outcome.DOWN:
        return result
    control = await control_probe().run(
        ProbeContext(spec=CONTROL_ENDPOINT, http=transport, clock=clock, session=session)
    )
    return apply_control_gate(result, control_ok=control.outcome is Outcome.UP)


def read_config() -> Config | None:
    try:
        return Config.from_environ()
    except ConfigError as error:
        sys.stderr.write(f"no database configured ({error}), measuring without writing" + NEWLINE)
        return None


def build_store(config: Config | None) -> Store | None:
    """The store is optional: without its two variables the loop measures and writes nothing."""
    if config is None:
        return None
    return SupabaseStore(url=config.supabase_url, service_role_key=config.service_role_key)


async def _run_scheduler(specs: Sequence[ProbeSpec]) -> int:
    transport = HttpxTransport()
    config = read_config()
    store = build_store(config)
    region = config.region if config is not None else DEFAULT_REGION
    if config is not None and config.health_port is not None:
        # A platform that only keeps HTTP containers alive gets its endpoint; the loop is unchanged.
        start_health_server(config.health_port)
    scheduler = Scheduler(
        http=transport,
        clock=SystemClock(),
        specs=specs,
        emit=lambda spec, result: write_result(spec, result, verbose=False),
        store=store,
        region=region,
    )
    try:
        await scheduler.run_forever()
    finally:
        await transport.aclose()
        if isinstance(store, SupabaseStore):
            await store.aclose()
    return EXIT_OK


def write_result(spec: ProbeSpec, result: CheckResult, *, verbose: bool) -> None:
    """One JSON line per check, so the logs are also the thing `anden9 logs` reads."""
    line: dict[str, object] = {
        "probe": spec.probe_id,
        "outcome": result.outcome.value,
        "reason": result.reason.value,
        "http_status": result.http_status,
        "duration_ms": result.duration_ms,
        "retry_after_s": result.retry_after_s,
    }
    if verbose:
        line["method"] = spec.method
        line["url"] = spec.url
        line["timeout_s"] = spec.timeout_s
        line["degraded_ms"] = spec.degraded_ms
    sys.stdout.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")


def tail_logs() -> int:
    for raw in sys.stdin:
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except json.JSONDecodeError:
            sys.stdout.write(f"{LOG_PREFIX}{stripped}\n")
            continue
        if not isinstance(entry, dict):
            sys.stdout.write(f"{LOG_PREFIX}{stripped}\n")
            continue
        probe = entry.get("probe", "?")
        outcome = entry.get("outcome", "?")
        reason = entry.get("reason", "?")
        status = entry.get("http_status")
        duration = entry.get("duration_ms")
        sys.stdout.write(f"{probe:<14} {outcome:<9} {reason:<15} {status} {duration} ms\n")
    return EXIT_OK
