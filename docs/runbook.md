# Runbook

How to run this project, what to do when something breaks, and what is still missing. Anything not
yet verified says so explicitly.

## Local stack

Prerequisites verified on the development machine: `uv 0.12.10`, Python 3.14.5, Node 24.22.1,
pnpm 11.4.0, Docker 29.9.3. GNU `make` and the Supabase CLI are **not** installed there; the CLI
arrives through `npx supabase`.

```bash
python scripts/check.py          # every check, no GNU make needed
make check                       # same runner, on a machine with make (CI uses this)
```

| Step | Protects |
| --- | --- |
| `prober: lint` | style, magic numbers, banned `print`, security lint |
| `prober: types` | `mypy --strict` over sources, tests and the guard scripts |
| `prober: tests` | the domain rules, the probes, the transport and the scheduler |
| `prober: architecture` | the layer contracts: domain pure, probes on ports, adapters as leaves |
| `prober: request budget` | under 150 requests per hour to Renfe |
| `web: types` | TypeScript `strict`, no unchecked index access |
| `web: lint` | no `useEffect`, no direct Supabase import outside `src/data`, no magic numbers |
| `web: tests` | Vitest on the components and the shared contract cases |
| `web: architecture` | feature isolation and the data layer boundary |
| `repo: hygiene` | no secret file, no banned dependency, no Renfe data or brand asset, no em dash |

## Running the prober

```bash
cd prober
uv run anden9 probe once live-map --verbose   # one check, no database writes
uv run anden9 probe once --all                # the eight endpoints, once
uv run anden9 run --catalog dev               # the loop, reduced catalog
uv run anden9 run --catalog full              # the loop, everything
uv run anden9 logs                            # pretty prints the JSON lines on stdin
```

Polling the real Renfe is capped on purpose: at most once every five minutes per person, never in a
loop, and the full scheduler runs only on the host.

## Database

```bash
npx supabase start      # local Postgres and API
npx supabase db reset   # reload migrations and seed
npx supabase status     # local keys and URLs
```

The prober writes with the `service_role` key; the web reads views with the anon key. `anon` cannot
select a table and cannot write anything, and a test proves it.

## Deployment

Everything here is prepared; only Albert can run it, because it needs his VPS, his Supabase cloud
project and his Netlify account.

### Prober on the VPS

```bash
# once, as root
useradd --system --create-home anden9
mkdir -p /opt/anden9 /etc/anden9
chmod 700 /etc/anden9
# copy the repository to /opt/anden9, on the branch that is being deployed
cp /opt/anden9/deploy/prober.env.example /etc/anden9/prober.env
chmod 600 /etc/anden9/prober.env
# fill SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and ANDEN9_REGION in that file

cd /opt/anden9 && docker compose --file deploy/docker-compose.yml build

cp deploy/anden9-prober.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now anden9-prober
systemctl status anden9-prober
docker compose --file /opt/anden9/deploy/docker-compose.yml logs --tail 50
```

Update:

```bash
cd /opt/anden9 && git pull --ff-only
docker compose --file deploy/docker-compose.yml build
systemctl restart anden9-prober
```

Stop: `systemctl disable --now anden9-prober`.

Roll back: `git checkout <previous tag or commit>`, rebuild and restart. The database is untouched
by a code rollback, and migrations are additive, so an older image keeps working.

### Web on Netlify

1. New site from the repository, base directory respected by `web/netlify.toml`.
2. Environment variables in the Netlify dashboard: `VITE_SUPABASE_URL` and
   `VITE_SUPABASE_ANON_KEY`. The anon key is public by design; the `service_role` key must never
   appear here.
3. Deploy. The SPA redirect is already in `web/netlify.toml`.

### Heartbeat alert

`.github/workflows/heartbeat.yml` runs every fifteen minutes, reads `v_heartbeat` with the anon key
and opens one issue when a region has been silent for more than ten minutes. It needs two
repository secrets: `SUPABASE_URL` and `SUPABASE_ANON_KEY`. Without them the job logs that it is
unconfigured and does nothing.

## Rotating keys

| Secret | Where it may live | Never |
| --- | --- | --- |
| `SUPABASE_SERVICE_ROLE_KEY` | `/etc/anden9/prober.env` on the host | in the web bundle, in logs, in git |
| `SUPABASE_URL` | host and Netlify | not a secret, still not hardcoded in features |
| Supabase anon key | Netlify and the heartbeat workflow secrets | anywhere in the prober |
| Renfe public API key and token | memory of the prober process | logs, database, exceptions |

Rotation: write the new value into the host file, `systemctl restart anden9-prober`, confirm one
green check and a fresh heartbeat, then remove the old value from the Supabase dashboard. If the
`service_role` key leaked, rotate it first and only then look at the logs.

## When Renfe changes something

1. Compare the live response with the canned answer the probe test uses in
   `prober/tests/test_probes.py`.
2. Read recent commits of `renfe-cli` for the affected endpoint.
3. Report the observed difference before touching the parser, and never relax validation just to
   make a probe green.

A sustained `bad_shape` opens an incident, which is the page telling us the parser is stale.

## When the prober stops measuring

The heartbeat view turns `is_stale` true after ten minutes and the scheduled workflow opens an
issue. The page shows "sin datos" for the gap, never invented uptime.

Order of checks: `systemctl status anden9-prober`, then the container logs, then
`docker run --rm anden9-prober:local probe once control` to prove the host has a network at all.

## When Renfe blocks the prober

A 403, a 429 or a protection page is `blocked`: it never counts as downtime and it is never retried
with another identity. Do not change the User-Agent, do not add a browser, do not rotate IPs.

What to do: read the reason in the logs, wait for the block to lift, and if it persists for days
reduce the interval of the affected probe in the catalog (with its commit and a fresh `make check`)
and mention it in the methodology page. A block is reported to the public, not hidden.

## Not verified yet

- `make check` on this machine: GNU make is not installed. The target runs the same
  `scripts/check.py` that is verified here, and CI runs the real `make check` on Ubuntu.
- The VPS, the Supabase cloud project and the Netlify site: created and deployed by Albert.
- The image on a Linux host: it is built and run here with Docker Desktop, see the M5 document.
