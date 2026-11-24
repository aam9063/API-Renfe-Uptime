"""Run every check this repository promises, with or without GNU make."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBER = ROOT / "prober"
WEB = ROOT / "web"
REQUIRED_TOOLS = ("uv", "pnpm")


@dataclass(frozen=True, slots=True)
class Step:
    """One command whose non-zero exit code is a broken promise."""

    name: str
    command: tuple[str, ...]
    cwd: Path


def steps() -> tuple[Step, ...]:
    return (
        Step("prober: lint", ("uv", "run", "ruff", "check", ".", "../scripts"), PROBER),
        Step("prober: types", ("uv", "run", "mypy", "src", "tests", "../scripts"), PROBER),
        Step("prober: tests", ("uv", "run", "pytest"), PROBER),
        Step("prober: architecture", ("uv", "run", "lint-imports"), PROBER),
        Step(
            "prober: request budget",
            ("uv", "run", "python", "../scripts/request_budget.py"),
            PROBER,
        ),
        Step("web: types", ("pnpm", "typecheck"), WEB),
        Step("web: lint", ("pnpm", "lint"), WEB),
        Step("web: tests", ("pnpm", "test"), WEB),
        Step("web: architecture", ("pnpm", "arch"), WEB),
        Step("repo: hygiene", (sys.executable, "scripts/repo_hygiene.py"), ROOT),
    )


def missing_tools() -> list[str]:
    return [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]


def main() -> int:
    absent = missing_tools()
    if absent:
        sys.stdout.write(f"FAIL missing tools: {', '.join(absent)}\n")
        return 1

    for step in steps():
        sys.stdout.write(f"\n==> {step.name}\n")
        sys.stdout.flush()
        executable = shutil.which(step.command[0])
        if executable is None:
            sys.stdout.write(f"\nFAIL {step.name}: {step.command[0]} is not installed\n")
            return 1
        completed = subprocess.run(
            (executable, *step.command[1:]),
            cwd=step.cwd,
            check=False,
        )
        if completed.returncode != 0:
            sys.stdout.write(f"\nFAIL {step.name} (exit {completed.returncode})\n")
            return completed.returncode or 1

    sys.stdout.write("\nAll checks passed.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
