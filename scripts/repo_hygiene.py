"""Repository guards that are cheaper as a script than as a third tool.

Every check prints one line. A failing check exits non-zero, so CI is red before a
secret, a Renfe brand asset or a browser dependency reaches a pull request.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EM_DASH = "\u2014"
IGNORED_DIRECTORIES = frozenset({".git", "node_modules", ".venv", "dist", ".evidence"})
SECRET_SUFFIXES = (".pem", ".key")
SECRET_PREFIXES = (".env",)
GITIGNORE_REQUIRED_ENTRIES = (".env", "*.pem", "*.key")
BANNED_PROBER_DEPENDENCIES = (
    "playwright",
    "selenium",
    "undetected-chromedriver",
    "cloudscraper",
    "curl-cffi",
    "curl_cffi",
    "captcha",
    "proxy-rotation",
)
COPY_ROOTS = (Path("web/src"), Path("docs"), Path("README.md"))
COPY_SUFFIXES = (".ts", ".tsx", ".css", ".md", ".json", ".html")
BRAND_ROOTS = (Path("web"), Path("docs"))
BRAND_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".pdf")
DATA_SUFFIXES = (".zip", ".gtfs", ".pbf")


class Report:
    """Collects one line per check and remembers whether anything failed."""

    def __init__(self) -> None:
        self.failures: list[str] = []

    def ok(self, name: str, detail: str) -> None:
        self.line(f"OK {name}: {detail}")

    def fail(self, name: str, detail: str) -> None:
        self.failures.append(name)
        self.line(f"FAIL {name}: {detail}")

    @staticmethod
    def line(text: str) -> None:
        sys.stdout.write(f"{text}\n")


def tracked_files() -> list[Path]:
    """Versioned files, or every file outside the ignored directories when git is absent."""
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return _walk(ROOT)
    return [ROOT / name for name in completed.stdout.split("\0") if name]


def _walk(directory: Path) -> list[Path]:
    files: list[Path] = []
    for path in directory.rglob("*"):
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def _relative(paths: Iterable[Path]) -> list[str]:
    return sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in paths)


def check_secrets(report: Report, files: Sequence[Path]) -> None:
    leaked = [
        path
        for path in _relative(files)
        if path.rsplit("/", maxsplit=1)[-1].startswith(SECRET_PREFIXES)
        or path.endswith(SECRET_SUFFIXES)
    ]
    if leaked:
        report.fail("secrets", f"versioned secret files: {', '.join(leaked)}")
        return
    ignore_file = ROOT / ".gitignore"
    text = ignore_file.read_text(encoding="utf-8") if ignore_file.exists() else ""
    missing = [entry for entry in GITIGNORE_REQUIRED_ENTRIES if entry not in text]
    if missing:
        report.fail("secrets", f".gitignore lost: {', '.join(missing)}")
        return
    report.ok("secrets", "no secret file is versioned and .gitignore still covers them")


def check_banned_dependencies(report: Report) -> None:
    manifest = ROOT / "prober" / "pyproject.toml"
    text = manifest.read_text(encoding="utf-8").lower()
    found = [name for name in BANNED_PROBER_DEPENDENCIES if name in text]
    if found:
        report.fail("honest identity", f"banned dependency in prober: {', '.join(found)}")
        return
    report.ok("honest identity", "no browser automation, captcha or proxy rotation dependency")


def check_no_data_dumps(report: Report, files: Sequence[Path]) -> None:
    dumps = [path for path in _relative(files) if path.endswith(DATA_SUFFIXES)]
    if dumps:
        report.fail("no Renfe data", f"versioned data files: {', '.join(dumps)}")
        return
    report.ok("no Renfe data", "no Renfe data file is versioned")


def check_copy(report: Report) -> None:
    offenders: list[str] = []
    for root in COPY_ROOTS:
        target = ROOT / root
        if not target.exists():
            continue
        candidates = [target] if target.is_file() else _walk(target)
        for path in candidates:
            if path.suffix not in COPY_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if EM_DASH in text:
                offenders.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    if offenders:
        report.fail("Spanish copy", f"em dash in: {', '.join(sorted(offenders))}")
        return
    report.ok("Spanish copy", "no em dash in web copy or docs")


def check_brand_assets(report: Report, files: Sequence[Path]) -> None:
    branded = [
        path
        for path in _relative(files)
        if any(path.startswith(f"{root}/") for root in BRAND_ROOTS)
        and path.lower().endswith(BRAND_SUFFIXES)
        and "renfe" in path.lower()
    ]
    if branded:
        report.fail("no brand assets", f"Renfe asset committed: {', '.join(branded)}")
        return
    report.ok("no brand assets", "no Renfe logo or brand asset in the repository")


def main() -> int:
    report = Report()
    files = tracked_files()
    check_secrets(report, files)
    check_banned_dependencies(report)
    check_no_data_dumps(report, files)
    check_copy(report)
    check_brand_assets(report, files)
    if report.failures:
        sys.stdout.write(f"\n{len(report.failures)} hygiene check(s) failed\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
