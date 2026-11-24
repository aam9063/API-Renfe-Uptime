# Runbook

How to run this project, what to do when something breaks, and what is still missing. Anything
not yet verified says so explicitly.

## Local stack

Prerequisites verified on the development machine: `uv 0.12.10`, Python 3.14.5, Node 24.22.1,
pnpm 11.4.0, Docker 29.9.3. GNU `make` and the Supabase CLI are **not** installed there.

```bash
python scripts/check.py          # every check, no GNU make needed
make check                       # same runner, on a machine with make (CI uses this)
```

Checks and what each one protects:

| Step | Protects |
| --- | --- |
| `prober: lint` | style, magic numbers, banned `print`, security lint |
| `prober: types` | `mypy --strict` over sources, tests and the guard scripts |
| `prober: tests` | the domain rules and the catalog |
| `prober: architecture` | the layer contracts: domain pure, probes on ports, adapters as leaves |
| `prober: request budget` | under 150 requests per hour to Renfe |
| `web: types` | TypeScript `strict`, no unchecked index access |
| `web: lint` | no `useEffect`, no direct Supabase import outside `src/data`, no magic numbers in features |
| `web: tests` | Vitest on the components |
| `web: architecture` | feature isolation and the data layer boundary |
| `repo: hygiene` | no secret file, no banned dependency, no Renfe data or brand asset, no em dash in Spanish copy |

## Database

```bash
npx supabase start      # local Postgres and API
npx supabase db reset   # reload migrations and seed
npx supabase status     # local keys and URLs
```

Migrations and views arrive in M3. Today `supabase/config.toml` exists and nothing else.

## Probe against the real Renfe

At most once every five minutes per session, never in a loop, never as part of the test suite:

```bash
cd prober && uv run anden9 probe once live-map --verbose
```

Probe commands land in M2. If a probe answers `blocked`, stop calling that endpoint for the rest
of the session and report it: never retry with other headers, another user agent, another IP or
a headless browser.

## When Renfe changes something

1. Compare the live response with the recorded fixture in `prober/tests/fixtures/http/`.
2. Read recent commits of `renfe-cli` for the affected endpoint.
3. Report the observed difference before touching the parser, and never relax validation just to
   make a probe green.

## When the prober stops measuring

The heartbeat table and the public view tell the truth ("sin datos"), and M5 adds the banner and
the scheduled workflow that opens an issue after ten minutes of silence. Until then, check the
prober logs and the heartbeat row by hand.

## Secrets

| Secret | Where it may live | Never |
| --- | --- | --- |
| `SUPABASE_SERVICE_ROLE_KEY` | prober environment on the host | in the web bundle, in logs, in git |
| `SUPABASE_URL` | prober and web build | not a secret, still not hardcoded in features |
| Supabase anon key | web build only | anywhere in the prober |
| Renfe public API key and token | memory of the prober process | logs, database, exceptions |

Rotation: replace the value in the host environment, restart the prober, confirm the heartbeat
and one green check, then remove the old value. `scripts/repo_hygiene.py` fails if a secret file
or a banned identity dependency reaches a pull request.

## Not verified yet

- `make check` on this machine: GNU make is not installed. The target runs the same
  `scripts/check.py` that is verified here.
- The GitHub Actions workflow: the repository has no remote yet, so the workflow has never run.
- Deployment, systemd unit, Docker image and Netlify: M5, and owned by Albert.
