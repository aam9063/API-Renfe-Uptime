# M3: persistence, views and the store

Feature document for milestone M3 of `BRIEF.md` section 12. Work in this document belongs to one
writer working in its own worktree (`feat/m3-persistence`).

## Specs

S1 (scope, verbatim from `BRIEF.md` §12):

> - Migraciones de la sección 7, RLS, vistas, retención; adaptador `store_supabase`; heartbeat.
> - Los casos de `contracts/uptime_cases.json` se ejecutan contra las vistas en un Supabase local (`supabase start`).

S2 (acceptance, verbatim):

> **Aceptación:** con la sonda corriendo 30 minutos contra un Supabase local, las vistas devuelven datos coherentes; un test demuestra que la clave anónima no puede escribir en ninguna tabla ni leer tablas crudas. Se resuelve la incertidumbre 10. **Riesgo alto en RDD.**

S3 (schema, verbatim from `BRIEF.md` §7):

```
probes      (id text pk, name, group_name, host, method, url_display, interval_s, timeout_s,
             degraded_ms, enabled bool, retired_at timestamptz null, sort int)
checks      (id bigint pk, probe_id fk, started_at timestamptz, duration_ms int,
             http_status int null, outcome outcome_enum, reason text, region text,
             probe_version text)
incidents   (id bigint pk, probe_id fk, kind outcome_enum, started_at, ended_at null,
             checks_count int)
heartbeat   (region text pk, last_seen timestamptz, probe_version text)
```

S4 (views, verbatim from `BRIEF.md` §7):

> Vistas públicas (la web solo lee estas): `v_status_now`, `v_uptime_windows` (24 h, 7, 30 y 90 días, con uptime, nueves y segundos por estado), `v_daily_90` (peor estado y uptime por día), `v_latency_24h` (p50 y p95 cada 30 minutos), `v_recent_checks` (últimas 50 por sonda), `v_incidents`.
> - RLS: `anon` solo puede `select` sobre las vistas. Ninguna tabla es escribible con la clave anónima. La sonda escribe con la `service_role`, que solo existe en el entorno del VPS.
> - Retención: `checks` crudos 120 días; rollups diarios para siempre.

S5 (formula, verbatim from `BRIEF.md` §5.2). The views are the single runtime home of the formula:

> - Cada comprobación cubre el intervalo desde su inicio hasta la siguiente, con un máximo de 2 veces su intervalo nominal. Lo que quede sin cubrir es `unknown` con reason `gap`.
> - `uptime = (s_up + s_degraded) / (s_total - s_blocked - s_unknown)`, en segundos enteros.
> - `nueves = floor(-log10(1 - uptime))`. Si no hubo ningún segundo caído, no hay nueves que calcular: se muestra "sin caídas".
> - Si el denominador es menor que el 50 % de la ventana, la ventana se marca como "datos insuficientes" y no se muestran nueves.
> - Los porcentajes se truncan (no se redondean) a dos decimales.

S6 (contract): `contracts/uptime_cases.json` is the shared truth. The eleven cases must pass
against the SQL implementation, with the same `denominator_seconds`, `down_seconds`, `nines`,
`insufficient` and `display_percent` as the Python specification in
`prober/src/anden9/domain/uptime.py`.

## Tasks

| ID | Task | Specs | Commit |
| --- | --- | --- | --- |
| T1 | Schema migrations: enum, four tables, indexes, the `probes` catalog sync | S3 | `feat(db): add the measurement schema` |
| T2 | The formula in SQL: coverage with `lead()`, uptime, nines, truncation, insufficient window, as functions the views call | S5 | `feat(db): add the uptime functions` |
| T3 | The public views of the brief | S4, S5 | `feat(db): add the public views` |
| T4 | RLS: `anon` reads views only, `service_role` writes, tables unreadable by `anon` | S4 | `feat(db): restrict anon to the public views` |
| T5 | Retention: raw checks 120 days, daily rollups kept | S4 | `feat(db): add the retention jobs` |
| T6 | Seed with a week of synthetic checks, incidents and a heartbeat, enough for the web and e2e | S1 | `chore(db): seed a week of measurements` |
| T7 | `store_supabase` adapter: write a check, open and close an incident, beat the heartbeat | S1 | `feat(adapters): write checks, incidents and the heartbeat` |
| T8 | Contract test: the eleven cases against the SQL functions and one end-to-end through a view | S1, S6 | `test(db): run the uptime contract against the views` |
| T9 | RLS test: `anon` cannot write any table and cannot read a raw table | S2 | `test(db): prove anon cannot write or read tables` |

## Rules for the writer

- Work only in this worktree (`feat/m3-persistence`). Do not touch `web/`, `docs/`, `README.md`,
  `odd/`, root `Makefile`, `.github/`, `scripts/`.
- Allowed edit surfaces: `supabase/`, `prober/src/anden9/adapters/store_supabase.py`,
  `prober/src/anden9/domain/`, `prober/tests/`, `prober/pyproject.toml`, `prober/uv.lock`,
  `contracts/`.
- Never drop or rewrite `checks` or `incidents` data in a migration. Only additive migrations.
- The enum values are `up`, `degraded`, `down`, `blocked`, `unknown` and the reasons are the ones
  in `prober/src/anden9/domain/outcome.py`.
- Tests that need a database are marked `integration` and skipped when
  `ANDEN9_LOCAL_DB_URL` is unset, so `pytest` stays green without Docker.
- `uv run ruff check . ../scripts`, `uv run mypy src tests`, `uv run pytest` and
  `uv run lint-imports` must pass. `uv run lint-imports` forbids the domain importing `supabase`:
  the client lives in the adapter only.
- Commit in the units of the task table with Conventional Commits, and say in the final answer
  which tasks and specs are covered and what could not be verified.

## Log

### L1 (original request, verbatim)

> puedes lanzar agentes en paralelo que vayan adelantando faena y no se pisen los unos con los otros?

### L2 (decisions)

- **The formula lives in SQL functions, and the views only glue.** `public.uptime_seconds(...)`
  and friends let the contract test feed the eleven cases exactly as written, while the views
  compute the seconds per state from real rows. One implementation, two entry points.
- **Uncertainty 10** (Supabase free-plan limits with ~350 000 checks) is answered with numbers in
  this document, measured locally, not with a guess.
