# Andén 9

**No oficial · sin relación con Renfe.**

An unofficial status page that measures the uptime of the Renfe APIs used by
[`renfe-cli`](https://github.com/luisgonzaleznf/renfe-cli) and publishes it the way a SaaS
publishes an SLA: uptime per window, latency percentiles, incidents and a number of **nines**
(99.9 % = 3 nines).

A wrong number is worse than no number. When the data is unclear the published outcome is
`unknown`, never a guess.

- What to build and in which order: [`BRIEF.md`](BRIEF.md)
- Permanent operating rules for agents: [`AGENTS.md`](AGENTS.md)
- Design source of the four screens: [`design/`](design)

## Project status

Living table, updated with every implementation step. Nothing is listed as done until its
acceptance check has been observed.

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 | Scaffolding and constraints: monorepo, check runner, canonical templates, docs, guards, CI | built, awaiting review |
| M1 | Measurement domain without network: classifier rules, incident tracker, uptime contract cases | built, awaiting review |
| M2 | Real probes and scheduler: HTTP adapter, 8 probes, control endpoint, budget, `Retry-After` | built, awaiting review |
| M3 | Persistence and views: migrations, RLS, public views, Supabase store, heartbeat | pending |
| M4 | Web: four screens, responsive, views only, seeds and Playwright evidence | pending |
| M5 | Deployment and operation: Docker, systemd, Netlify, runbook, heartbeat alert | built, awaiting review |

M0 is [pull request #1](https://github.com/aam9063/API-Renfe-Uptime/pull/1) against `dev`, with
the first CI run green on all three jobs: `make check` on Ubuntu, the same runner on Windows, and
Playwright. The native review refused that candidate for size (`lens_context_budget_exceeded`,
64 files and 6640 changed lines), so the pull request carries no review outcome yet.

## What is in place today

- **Prober** (`prober/`): `uv` project, Python 3.14, `mypy --strict`, ruff with magic number and
  security rules, pytest, and four import-linter contracts that keep the domain pure, the probes
  on ports and the adapters as leaves.
- **Measurement vocabulary and catalog** (`prober/src/anden9/domain`, `probes/catalog.py`): the
  five states, the stable reasons, the eight measured endpoints plus the control endpoint, and
  the request budget as data. Budget today: 116 requests per hour to Renfe.
- **Measurement domain** (`prober/src/anden9/domain`): payload states, bot page detection that can
  only downgrade a would-be `down` to `blocked`, the control endpoint gate, interval coverage with
  honest gaps, exact `Fraction` uptime with truncated display, the nines of the downtime ratio, and
  the incident machine that opens after two failures of a kind and closes after two successes.
  `contracts/uptime_cases.json` holds eleven shared cases, and hypothesis pins the properties.
- **Canonical probe template** (`probes/_template.py`): copy it, register the catalog entry, done.
  Timeout from the catalog, one request, no retry, classification delegated to the domain.
- **Guards** (`scripts/`): `check.py` runs every check with or without GNU make,
  `request_budget.py` fails the build when the catalog gets impolite, `repo_hygiene.py` fails on
  a versioned secret, a browser automation dependency, a Renfe data file, a brand asset or an em
  dash in Spanish copy.
- **Web** (`web/`): Vite, React 19, TypeScript `strict` with `noUncheckedIndexedAccess` and
  `exactOptionalPropertyTypes`, Tailwind 4 with the design palette and the three typefaces of the
  design, ESLint banning `useEffect` and direct Supabase imports, Vitest, Playwright, and
  dependency-cruiser enforcing feature isolation. Data layer: TanStack Query provider in place.
- **Docs** (`docs/`): feature map, probe catalog, runbook, glossary.
- **CI** (`.github/workflows/check.yml`): `make check` on Linux, the same checks on Windows, and a
  Playwright job. Never runs `make check` against real Renfe.

- **Probes, transport and scheduler** (`prober/src/anden9/probes`, `adapters`, `scheduler.py`): the
  eight Renfe endpoints plus the control endpoint, an `httpx` transport with one lock per host and
  every transport error mapped, a scheduler that runs what is due, gates a `down` behind the
  control endpoint and pauses a probe on `Retry-After`, and a CLI with `probe once`, `run` and
  `logs`.

- **Deployment and operation** (`prober/Dockerfile`, `deploy/`, `web/netlify.toml`,
  `.github/workflows/heartbeat.yml`): a non-root image with the dependencies in their own layer, a
  compose file with log rotation, a systemd unit that keeps the container alive, the Netlify
  configuration with the SPA redirect, and a scheduled job that opens an issue when the heartbeat
  goes silent for more than ten minutes. The runbook covers start, stop, update, rollback and key
  rotation.

Still missing on purpose: migrations, views, the store adapter, and the four screens.

## How measurement works

Short version, the full method is a public page:

| State | When | Counts as available? |
| --- | --- | --- |
| `up` | Expected status, valid payload, latency under the degraded threshold | yes |
| `degraded` | Valid but slow, or empty/old data when it should not be | yes, shown apart |
| `down` | Timeout, refused, DNS/TLS error, 5xx, invalid payload shape | yes, against |
| `blocked` | 403, 429, protection page or waiting room | excluded from the denominator |
| `unknown` | The prober itself failed, control endpoint failed, or no check covered the interval | excluded from the denominator |

- `uptime = (s_up + s_degraded) / (s_total - s_blocked - s_unknown)`, in whole seconds.
- `nines = floor(-log10(1 - uptime))`; no downtime at all is reported as "sin caídas", never as
  infinite nines.
- Percentages are truncated to two decimals, not rounded.
- The formula lives in one place: the SQL views. The web only formats.

Fairness to Renfe is a constraint, not a preference: no probe below 60 s, heavy probes not below
900 s, one in-flight request per host, fewer than 150 requests per hour in total, and an honest
User-Agent (`anden9-probe/<version>`). A block is reported as `blocked` and never retried with a
different identity.

## Repository layout

```
prober/       Python 3.14 service and CLI that measures Renfe
web/          React 19 + TypeScript SPA that reads public views
supabase/     Postgres migrations, RLS and public views
contracts/    uptime_cases.json, shared by the SQL views and the web formatter
design/       HTML source of the four screens
docs/         feature map, probes, runbook, glossary
scripts/      check runner, request budget, repository hygiene
odd/          feature documents for substantial work
evals/        skill evaluations
```

## Local development

Prerequisites: `uv`, `pnpm`, Node 22+, Docker (for local Supabase). GNU `make` is optional: the
runner is a Python script.

```bash
python scripts/check.py    # every check, on any OS
make check                 # same runner, on a machine with make
```

Full stack, once M3 and M4 land:

```bash
npx supabase start                                        # local Postgres and API
cd prober && uv run anden9 run --catalog dev              # reduced catalog: live-map, www-search
cd web && pnpm dev                                        # http://localhost:5173
cd web && pnpm e2e                                        # Playwright, desktop and mobile
```

One-shot check against the real Renfe, at most once every 5 minutes and never in a loop:

```bash
cd prober && uv run anden9 probe once live-map --verbose
```

## Git flow

```
main  <- Albert merges by hand
 dev  <- Albert merges by hand, every PR
  feat/<slug>   fix/<slug>   chore/<slug>   <- agents branch from dev
```

Atomic PRs against `dev`, Conventional Commits with the area as scope
(`feat(probes): add live-map probe`). Agents never merge, never push to `main` or `dev`, and
never force-push a shared branch.

## Credits and licence

Endpoint knowledge comes from [`renfe-cli`](https://github.com/luisgonzaleznf/renfe-cli) by
Luis González (MIT). This project is not affiliated with Renfe, uses no Renfe branding, and
shows the "No oficial · sin relación con Renfe" notice on every route.
