"""Command line entry point. Probe and scheduler commands arrive in M2."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from anden9.version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="anden9", description="Unofficial Renfe API prober")
    parser.add_argument("--version", action="version", version=f"anden9-probe/{__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0
