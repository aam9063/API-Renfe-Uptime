# M4: the four screens

Feature document for milestone M4 of `BRIEF.md` section 12. Work in this document belongs to one
writer working in its own worktree (`feat/m4-web`).

## Specs

S1 (scope, verbatim from `BRIEF.md` §12):

> - Las cuatro pantallas del diseño, responsive, leyendo solo de las vistas; estados de carga, error y "sin datos".
> - `supabase/seed/` con datos de ejemplo para desarrollo y e2e.

S2 (acceptance, verbatim):

> **Aceptación:** Playwright recorre portada, cambio de ventana, detalle de servicio y metodología con datos semilla, en escritorio (1440) y móvil (390), con capturas adjuntas al PR; axe sin violaciones serias; el aviso "No oficial" aparece en todas las rutas.

S3 (design source): `design/Main.dc.html` (home desktop), `design/Servicio.dc.html` (service
detail), `design/Metodologia.dc.html` (methodology), `design/Movil.dc.html` (home mobile). The
palette and the three typefaces (`Space Grotesk`, `Inter`, `JetBrains Mono`) are already wired as
Tailwind tokens in `web/src/index.css`: use those token names, never raw hex values.

S4 (data access, verbatim from `AGENTS.md` §5.1): React 19 data access goes through TanStack Query
hooks in `web/src/data/`; `useEffect` is banned in feature code; only `web/src/data/` imports the
Supabase client; the web reads views (`v_*`), never tables.

S5 (copy, verbatim from `AGENTS.md` §5.1): web copy in Spanish, no em dashes (U+2014), and the
notice "No oficial · sin relación con Renfe" on every route.

S6 (formatting, verbatim from `BRIEF.md` §5.2): the uptime and nines come from the views already
computed. The web only formats: percentages truncated to two decimals with the Spanish comma, and
"sin caídas" instead of infinite nines. `contracts/uptime_cases.json` is the shared truth and a
vitest test must run the shared formatting cases through `web/src/lib/format.ts`.

## Tasks

| ID | Task | Specs | Commit |
| --- | --- | --- | --- |
| T1 | `web/src/lib/format.ts`: percent truncation, duration, latency, nines label, driven by the shared contract cases | S6 | `feat(web): format percentages and durations from the contract` |
| T2 | `web/src/data/`: Supabase client, view queries and TanStack Query hooks for the four screens | S4 | `feat(web): add the view queries and their hooks` |
| T3 | Shell: header, footer, the unofficial notice on every route, and the router | S2, S5 | `feat(web): add the shell and the routes` |
| T4 | `status-overview`: aggregate card, window tabs, nines scale, grouped service list with the 90 day strip | S1, S3 | `feat(web): add the status overview` |
| T5 | `service-detail`: windows, latency, 90 days, rules and recent checks, retirement notice | S1, S3 | `feat(web): add the service detail` |
| T6 | `methodology`: states, formula, catalog read from the database, limits and honesty section | S1, S3 | `feat(web): add the methodology page` |
| T7 | `incidents`: list with kind, cause and duration, and the `#incidentes` anchor | S1, S3 | `feat(web): add the incidents list` |
| T8 | Loading, error and "sin datos" states for every screen | S1 | `feat(web): handle loading, error and no data` |
| T9 | Accessibility: axe with no serious or critical violations, real interactive elements | S2 | `test(web): check axe on every route` |
| T10 | Playwright: the four routes at 1440 and 390, evidence screenshots and the notice check | S2 | `test(web): walk the four routes and attach evidence` |

## Rules for the writer

- Work only in this worktree (`feat/m4-web`). Do not touch `prober/`, `supabase/`, `docs/`,
  `odd/`, root `Makefile`, `.github/`, `scripts/`, `contracts/`.
- Allowed edit surfaces: `web/`.
- Use the view columns as the M3 specification defines them:
  - `v_status_now(probe_id, name, group_name, host, outcome, reason, last_check_at, duration_ms)`
  - `v_uptime_windows(probe_id, window_key, window_label, uptime, display_percent, nines,
    down_seconds, denominator_seconds, insufficient, no_downtime)`
  - `v_daily_90(probe_id, day, worst_outcome, uptime, display_percent)`
  - `v_latency_24h(probe_id, bucket_start, p50_ms, p95_ms)`
  - `v_recent_checks(probe_id, started_at, outcome, http_status, duration_ms)`
  - `v_incidents(probe_id, kind, started_at, ended_at, duration_s, checks_count)`
  - `v_probes(id, name, group_name, host, method, url_display, interval_s, timeout_s,
    degraded_ms, retired_at, sort)`
- `web/src/data/` builds the Supabase client from `import.meta.env.VITE_SUPABASE_URL` and
  `VITE_SUPABASE_ANON_KEY`, and every hook must degrade to a clear "sin datos" state instead of
  throwing when those are missing. That is what keeps tests and e2e working without a database.
- For component tests, inject a query client with a stub `fetch`; never call a real network in
  `vitest`.
- Playwright runs the built app at 1440 and 390. When `VITE_SUPABASE_URL` is missing it must still
  walk the four routes and assert the notice and the "sin datos" state; when the local database is
  up it asserts real numbers from the seed.
- `pnpm typecheck`, `pnpm lint`, `pnpm test`, `pnpm arch`, `pnpm e2e` must pass. No new runtime
  dependency without a justification in the final answer.
- Commit in the units of the task table with Conventional Commits, and say in the final answer
  which tasks and specs are covered and what could not be verified.

## Log

### L1 (original request, verbatim)

> puedes lanzar agentes en paralelo que vayan adelantando faena y no se pisen los unos con los otros?

### L2 (decisions)

- **The web never computes.** Every number arrives from a view; `format.ts` only truncates, adds
  the comma and chooses the label. The shared contract cases keep that honest.
- **A missing configuration is a state, not a crash.** Without Supabase variables the app renders
  the shell and "sin datos", which is what a static preview and the e2e run need.
