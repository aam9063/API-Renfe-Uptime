# Feature map

Where every feature lives and how to reach it, so a vague report maps to code and to a
reproduction path. Update this file in the same pull request that adds, moves, renames or
removes a feature, route, probe, view, config key or `data-testid`.

Status legend: `built` (verified by a check), `pending` (milestone named), `planned`.

## status-overview

- What it is (user point of view): home page with the aggregate uptime, its nines and the list of services.
- Sub-features: aggregate card, window tabs (24h, 7d, 30d, 90d), nines scale panel, service list with 90 day bars, incidents link.
- How to reach it in the UI: `/`.
- Keyboard shortcuts: none yet.
- Selectors for programmatic control: no test ids; the e2e run drives it by role and link text.
- Code location: `web/src/features/status-overview/`.
- Backend/API involved: views `v_uptime_windows`, `v_status_now`, `v_daily_90`, `v_latency_24h`.
- Known pitfalls: the aggregate is the unweighted mean of active services; a service in `unknown` is excluded, never counted as down.
- Status: built (M4). Design: `design/Main.dc.html`.

## service-detail

- What it is (user point of view): one service with its windows, latency, 90 days, measurement rules and recent checks.
- Sub-features: window cards, p50 and p95 latency, daily strip, recent checks table, retirement notice for `legacy-shop`.
- How to reach it in the UI: `/servicio/:id`, from a row of the home list.
- Keyboard shortcuts: none yet.
- Selectors for programmatic control: no test ids; the e2e run drives it by role and link text.
- Code location: `web/src/features/service-detail/`.
- Backend/API involved: `v_uptime_windows`, `v_latency_24h`, `v_daily_90`, `v_recent_checks`, `v_incidents`.
- Known pitfalls: a retired probe is shown as "retirada", never as down.
- Status: built (M4). Design: `design/Servicio.dc.html`.

## methodology

- What it is (user point of view): how the numbers are measured, the five states, the formula, the probe catalog and the limits.
- Sub-features: state table, formula, catalog table read from `probes`, honesty section (region, user agent, no bypass).
- How to reach it in the UI: `/metodologia`.
- Keyboard shortcuts: none yet.
- Selectors for programmatic control: no test ids; the e2e run drives it by role and link text.
- Code location: `web/src/features/methodology/`.
- Backend/API involved: `probes` view exposing the catalog; no hand written catalog in the page.
- Known pitfalls: the catalog is data, never copy pasted HTML.
- Status: built (M4). Design: `design/Metodologia.dc.html`.

## incidents

- What it is (user point of view): recent incidents with kind, cause and duration.
- Sub-features: incident list, anchor `#incidentes` from the home page.
- How to reach it in the UI: home page section, anchor `#incidentes`.
- Keyboard shortcuts: none yet.
- Selectors for programmatic control: no test ids; the e2e run drives it by role and link text.
- Code location: `web/src/features/incidents/`.
- Backend/API involved: view `v_incidents`.
- Known pitfalls: a `blocked` stretch is shown apart and never counted as downtime.
- Status: built (M4).

## probes

- What it is (user point of view): one check per measured Renfe endpoint.
- Sub-features: eight probes plus the control endpoint, each one file.
- How to reach it in the UI: not in the UI; `cd prober && uv run anden9 probe once <id> --verbose`.
- Keyboard shortcuts: not applicable.
- Selectors for programmatic control: not applicable.
- Code location: `prober/src/anden9/probes/`, catalog in `probes/catalog.py`.
- Backend/API involved: the Renfe endpoints listed in `docs/probes.md`.
- Known pitfalls: one request per run, no retry, honest User-Agent, budget enforced by `scripts/request_budget.py`.
- Status: built (M2). `uv run anden9 probe once <id> --verbose` prints what it saw.

## classifier

- What it is (user point of view): the state published for each check.
- Sub-features: status and latency mapping (built), payload rules per probe, control endpoint gate, interval coverage (pending).
- How to reach it in the UI: indirectly, through every number on the page.
- Keyboard shortcuts: not applicable.
- Selectors for programmatic control: not applicable.
- Code location: `prober/src/anden9/domain/classifier.py`.
- Backend/API involved: none, pure code.
- Known pitfalls: a protection page is `blocked`, never `down`; a broken prober is `unknown`, never `down`.
- Status: status and latency mapping built (M0), rest pending (M1, M2).

## incident-tracker

- What it is (user point of view): the incidents listed on the page.
- Sub-features: open after 2 equal failures, close after 2 successes, duration from the first failure.
- How to reach it in the UI: `#incidentes`.
- Keyboard shortcuts: not applicable.
- Selectors for programmatic control: not applicable.
- Code location: `prober/src/anden9/domain/incidents.py` (pending).
- Backend/API involved: `incidents` table, `v_incidents` view.
- Known pitfalls: kinds are tracked separately, so a degraded stretch and a down stretch are different incidents.
- Status: pending (M1).

## scheduler

- What it is (user point of view): nothing directly; it decides when each probe runs.
- Sub-features: per probe interval, one in-flight request per host, request budget, `Retry-After` pause.
- How to reach it in the UI: not in the UI; `cd prober && uv run anden9 run --catalog dev`.
- Keyboard shortcuts: not applicable.
- Selectors for programmatic control: not applicable.
- Code location: `prober/src/anden9/scheduler.py`.
- Backend/API involved: none outbound except the probes it triggers.
- Known pitfalls: a 429 with `Retry-After` pauses the probe, it never triggers a retry. A `down` is only published when the control endpoint answered in the same minute.
- Status: built (M2).

## store

- What it is (user point of view): the numbers survive restarts.
- Sub-features: write checks, update heartbeat, incident bookkeeping.
- How to reach it in the UI: indirectly.
- Keyboard shortcuts: not applicable.
- Selectors for programmatic control: not applicable.
- Code location: `prober/src/anden9/adapters/store_supabase.py` (pending).
- Backend/API involved: `checks`, `incidents`, `heartbeat` tables.
- Known pitfalls: the `service_role` key is read only by `config.py` and never leaves the prober environment.
- Status: pending (M3).

## db-views

- What it is (user point of view): the numbers the page shows.
- Sub-features: `v_status_now`, `v_uptime_windows`, `v_daily_90`, `v_latency_24h`, `v_recent_checks`, `v_incidents`.
- How to reach it in the UI: every page.
- Keyboard shortcuts: not applicable.
- Selectors for programmatic control: not applicable.
- Code location: `supabase/migrations/` (pending).
- Backend/API involved: Postgres, RLS for `anon`.
- Known pitfalls: the formula lives here and only here; `contracts/uptime_cases.json` runs against it.
- Status: pending (M3).
