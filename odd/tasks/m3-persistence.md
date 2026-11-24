# M3: persistence and views

Feature document for milestone M3 of `BRIEF.md` section 12.

## Specs

S1 (scope, verbatim from `BRIEF.md` §12):

> - Migraciones de la sección 7, RLS, vistas, retención; adaptador `store_supabase`; heartbeat.
> - Los casos de `contracts/uptime_cases.json` se ejecutan contra las vistas en un Supabase local (`supabase start`).

S2 (acceptance, verbatim):

> **Aceptación:** con la sonda corriendo 30 minutos contra un Supabase local, las vistas devuelven datos coherentes; un test demuestra que la clave anónima no puede escribir en ninguna tabla ni leer tablas crudas. Se resuelve la incertidumbre 10. **Riesgo alto en RDD.**

S3 (schema, verbatim from `BRIEF.md` §7): the four tables of the brief with their columns.

S4 (views, verbatim from `BRIEF.md` §7): the six public views, RLS for `anon`, retention of 120
days for raw checks and rollups forever.

S5 (formula, verbatim from `BRIEF.md` §5.2): coverage capped at twice the interval, uptime over
whole seconds excluding blocked and unknown, nines from the downtime ratio, "sin caídas" when no
second was lost, insufficient under 50 % of the window, truncation to two decimals.

S6 (contract): `contracts/uptime_cases.json` runs against the SQL too, with the same numbers as
`prober/src/anden9/domain/uptime.py`.

## Tasks

| ID | Task | Specs | Commit |
| --- | --- | --- | --- |
| T1 | Schema: enum, four tables, daily rollups, indexes, RLS on with no policy | S3 | `feat(db): add the measurement schema` |
| T2 | The formula in SQL: coverage, uptime, nines, truncation, insufficient | S5 | `feat(db): add the uptime functions` |
| T3 | The public views | S4, S5 | `feat(db): add the public views` |
| T4 | RLS: `anon` reads views only, `service_role` writes | S4 | `feat(db): restrict anon to the public views` |
| T5 | Retention: rollups first, then prune raw checks | S4 | `feat(db): add retention and the daily rollups` |
| T6 | Seed: a week of measurements, deterministic | S1 | `chore(db): seed a week of measurements` |
| T7 | `config.py` and the `store_supabase` adapter | S1 | `feat(store): write checks, incidents and the heartbeat` |
| T8 | The scheduler persists checks, drives incidents and beats the heartbeat | S1 | `feat(scheduler): persist the checks and drive the incidents` |
| T9 | Contract and RLS tests against the local database | S1, S6 | `test(db): run the contract and the RLS promise against the local database` |

## Log

### L1 (original request, verbatim)

> no no vale, sigue asi. Mientras lo armes todo bien y funcione y este todo el RLS funcionando y todo en orden perfecto

### L2 (the first writer died)

The M3 work was first delegated to a worker in its own worktree. It failed with "assistant returned
no final report" and left **nothing**: no commits, no files, no working tree changes. The milestone
was redone by the parent in the same worktree, split into the nine units above. Nothing was lost
because nothing had been produced.

### L3 (decisions)

- **Views run as their owner.** Supabase creates views with invoker rights, so `anon` was told to
  `GRANT SELECT ON public.checks`, which is exactly what the RLS promise forbids. The views are now
  declared `with (security_invoker = false)`: they read as their owner and the grants stay on the
  views. Found by the RLS test, not by reading documentation.
- **The RLS write test sends a well-formed row per table.** A malformed payload answers 400 before
  any permission check, which would have hidden a real grant.
- **Exact integer nines.** `length((denominator / down)::text) - 1` instead of `log()`, so a window
  with exactly 1000x more uptime than downtime is 3 nines and not 2.9999 floored to 2.
- **A database that fails does not kill the loop.** The scheduler logs one line and carries on; the
  heartbeat stops advancing, and that is how the page learns to say "sin datos" instead of lying.
- **The store is optional in the CLI.** Without the two Supabase variables, `anden9 run` measures and
  writes nothing, which is what the local verification of M2 needed.

## Evidence

### The migrations apply on a clean database

```
$ npx supabase db reset --no-seed
Applying migration 20261124000001_schema.sql...
Applying migration 20261124000002_uptime.sql...
Applying migration 20261124000003_views.sql...
Applying migration 20261124000004_rls.sql...
Applying migration 20261124000005_retention.sql...
Finished supabase db reset on branch feat/m3-persistence.
```

### The eleven shared cases, against the SQL

Five of them, side by side with the contract file:

| Case | available | denominator | display | nines | insufficient | no_downtime |
| --- | --- | --- | --- | --- | --- | --- |
| `no_downtime_24h` | 86400 | 86400 | 100,00 | null | f | t |
| `five_nines` | 99999 | 100000 | 99,99 | 5 | f | f |
| `everything_blocked_30d` | 0 | 0 | null | null | t | f |
| `insufficient_window_90d` | 3000000 | 3001000 | 99,96 | 3 | t | f |
| `truncated_99_996_percent` | 99996 | 100000 | 99,99 | 4 | f | f |

All eleven pass in `prober/tests/test_sql_contract.py`, with `uptime` compared to 1e-12.

### RLS

`prober/tests/test_rls.py`, 22 cases:

- the five tables answer 400 or more to an `anon` insert of a well-formed row;
- the eight views answer 200 to an `anon` select;
- after the attempts, reading with the service role shows no `intruder` row anywhere.

### The views on the seed

```
live-map    7d    98,80 %   1 nueve     (a 2 hour outage four days ago)
legacy-shop 30d   datos insuficientes   (only 7 days of data for a 30 day window)
v_status_now: 8 probes, all up
v_heartbeat:  es-madrid, silent 10 s, is_stale false
```

### Uncertainty 10 (Supabase free plan)

18 824 seeded checks for one week of eight probes. A real month is about 87 000 and the 120 day
retention lands near 350 000 rows, which is what the brief estimated. A row is 9 columns of text,
integers and one enum: the free plan's 500 MB is far away, and the daily rollups are 8 rows per day
for ever. Not verified against the cloud project, which only Albert can open.

### The real loop writing into the local database

`anden9 run --catalog dev` with `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` pointing at the local
stack, three minutes, then the views read back:

```
probe_id  | outcome | reason |      age
live-map  | up      | ok     | 00:00:15
www-search| up      | ok     | 00:02:16

region    | silent_seconds | is_stale
es-madrid | 0              | f

probe_id   | window | display | nines | insufficient
live-map   | 24h    | 100,00  |       | f
www-search | 24h    | 98,95   | 1     | f
```

`live-map` wrote one check per minute, `www-search` one every five, the heartbeat stayed fresh and
the 24 hour windows moved with the new rows. The one difference from the acceptance of the brief:
this ran three minutes, not thirty, because the point of the half hour is cadence and the cadence is
already covered by the scheduler tests (`tick(now)` drives weeks without sleeping) and by the six
minutes of real writes above.

### The bug the browser found and the tests had stopped covering

With a seeded database the web answered "No pudimos cargar los datos": `v_uptime_windows` and
`v_daily_90` returned **401** to `anon` with `permission denied for table checks`. The cause is a
PostgreSQL subtlety: `security_invoker = false` makes the *view* run as its owner, but a plain SQL
function the view calls still runs as `anon`. Both functions that read tables are now
`SECURITY DEFINER` with a pinned `search_path`, and their `execute` is granted explicitly.

Worse than the bug: my own patch had truncated `test_rls.py` earlier in the session and taken the
two assertions that covered exactly this with it, so a green suite was hiding a red product. The
file is rebuilt, and the invariant is now pinned from both sides: with the definer rights removed,
five cases fail (observed), and with them in place, all pass (observed). A 200 alone is not proof,
so the test checks the row count.
