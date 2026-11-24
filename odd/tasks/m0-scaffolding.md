# M0: scaffolding and constraints

Feature document for milestone M0 of `BRIEF.md` section 12. Substantial work: monorepo,
toolchains, canonical templates, static guards, docs and CI.

## Specs

S1 (scope of the milestone, verbatim from `BRIEF.md` §12):

> - Monorepo con `prober/` (uv, ruff, mypy, pytest, import-linter) y `web/` (pnpm, Vite, TS estricto, ESLint, Vitest, Playwright, dependency-cruiser), `supabase/` inicializado.
> - Script raíz: `make check`, que ejecuta todo, más `scripts/repo-hygiene` y `scripts/request-budget`.
> - Plantillas canónicas: `prober/src/nueves/probes/_template.py` y `web/src/features/_template/`.
> - `docs/feature-map.md`, `docs/runbook.md`, `docs/glossary.md`, `docs/probes.md`.
> - CI en GitHub Actions para PRs hacia `dev`.

S2 (acceptance, verbatim):

> **Aceptación:** `make check` en verde en una rama limpia; una importación prohibida de prueba (dominio importando `httpx`) hace fallar import-linter; un intervalo de 30 s en el catálogo hace fallar el test de presupuesto.

S3 (directory structure, verbatim from `BRIEF.md` §4): the `prober/`, `web/`, `supabase/`,
`contracts/`, `docs/`, `odd/`, `scripts/` tree of the brief.

S4 (hard constraints that M0 must make enforceable at all, `AGENTS.md` §5.1): layer
boundaries via import-linter and dependency-cruiser, secrets never versioned, Spanish copy
without em dashes, no Renfe brand assets, `service_role` never in the web bundle, honest
User-Agent, request budget under 150 requests per hour.

S5 (language, `AGENTS.md` header): code, identifiers, commits and PRs in English; web copy in
Spanish without em dashes; reports to Albert in Spanish.

S6 (Git flow, `BRIEF.md` §11): agents branch from `dev` as `feat/<slug>`, open PRs against
`dev`, never merge and never push to `main` or `dev`.

## Tasks

| ID | Task | Specs | Route | Commit |
| --- | --- | --- | --- | --- |
| T1 | Repo hygiene, licence notice, README | S3, S5 | inline | `chore(repo): scaffold monorepo root` |
| T2 | Prober toolchain: uv, ruff, mypy strict, pytest, import-linter | S1, S4 | inline | `chore(prober): add toolchain and layer contracts` |
| T3 | Probe protocol, canonical template, catalog with the 8 entries and the control endpoint | S1, S4 | inline | `feat(prober): add probe catalog and template` |
| T4 | Root check runner, `Makefile`, `scripts/repo-hygiene`, `scripts/request-budget` | S1, S2, S4 | inline | `chore(scripts): add check runner and budget guards` |
| T5 | Web toolchain: Vite, TS strict, ESLint, Vitest, Playwright, dependency-cruiser, `_template` feature | S1, S4 | inline | `chore(web): add toolchain and feature template` |
| T6 | Supabase project and contracts directory | S1, S3 | inline | `chore(supabase): initialize project` |
| T7 | Docs: feature map, probes, runbook, glossary | S1 | inline | `docs: add feature map, probes, runbook and glossary` |
| T8 | GitHub Actions CI for PRs to `dev` | S1, S6 | inline | `chore(ci): add check workflow` |
| T9 | Observe acceptance: green `make check`, failing forbidden import, failing 30 s interval | S2 | inline | evidence, no commit |

All nine tasks are implemented; T9 records the observed evidence at the end of this document.
The work is not committed yet: the repository has no commits, no `dev` branch and no remote, so
the ODD work-unit commits wait for Albert's decision on the baseline.

## Log

### L1 (original request, verbatim)

> Vale dentro tienes el BRIEF y el AGENTS.md leelos para que sepas como tienes que proceder.
> Antes de nada crea el README.md el cual irás actualizando religiosamente cada vez que
> implementes algo hasta su final.

### L2 (decisions)

- **Environment facts (observed, not assumed).** `uv 0.12.10`, `Python 3.14.5`, `node v24.22.1`,
  `pnpm 11.4.0`, `docker 29.9.3` and `git 2.49.0` are installed on this machine. GNU `make` and
  the `supabase` CLI are **not**. Therefore `make check` delegates to `scripts/check.py`, and
  the same code is executed locally on Windows as `python scripts/check.py` and in CI as
  `make check` on `ubuntu-latest`. Nothing is verified on Linux before CI runs.
- **Domain skeleton in M0.** `anden9/domain/outcome.py` (the five states and the stable
  reasons) lands here because the `Probe` protocol, the template and the budget script need
  the type. All classification rules, incident state machine and interval coverage stay in
  M1.
- **Catalog split.** `probes/catalog.py` carries the measurement metadata for the eight
  endpoints (interval, timeout, degraded threshold, host) because the request-budget guard
  reads it. The probe callables per endpoint land in M2.
- **Git state.** The repository has no commits and no branches yet; `main` and `dev` do not
  exist. Work stays on the local branch until Albert confirms the remote and branch creation.

### L3 (product name, verbatim)

> se va a llamar 'Andén 9'

Applied to the whole repository before further building. Identifiers adopted, all of them
mechanical consequences of the brand:

| Where | Value |
| --- | --- |
| Brand in copy, docs and titles | `Andén 9` |
| Python distribution and import package | `anden9`, so `prober/src/anden9/` |
| CLI | `uv run anden9 probe once <id>` |
| npm package | `anden9-web` |
| User-Agent | `anden9-probe/<version> (+<site>/metodologia)` |
| Supabase `project_id` | `anden9` |

The Spanish word *nueves* (nines) stays as metric vocabulary: it is what the page counts, not
the product name. `AGENTS.md` and `BRIEF.md` keep their prose and their metric wording; only
their paths, CLI commands and User-Agent were updated to the new identifiers.

## Evidence

### T9 acceptance checks, observed on this machine

`python scripts/check.py` (the exact code `make check` runs) ends with `All checks passed.`:

| Step | Result |
| --- | --- |
| prober: lint | `All checks passed!` |
| prober: types | `Success: no issues found in 18 source files` |
| prober: tests | `21 passed` |
| prober: architecture | `Contracts: 4 kept, 0 broken.` |
| prober: request budget | `OK request budget: 116 requests per hour to Renfe (limit 150)` |
| web: types | `tsc --noEmit` clean |
| web: lint | `eslint .` clean |
| web: tests | `Test Files 1 passed (1)` |
| web: architecture | `no dependency violations found (9 modules, 8 dependencies cruised)` |
| repo: hygiene | five `OK` lines |

### A forbidden import breaks import-linter

Temporary `import httpx` appended to `domain/budget.py`, then `uv run lint-imports`:

```
The domain is pure: no HTTP client, no database, no settings BROKEN
-   anden9.domain.budget -> httpx (l.55)
Probes depend on ports, never on adapters or the HTTP library BROKEN
anden9.probes is not allowed to import httpx:
-   anden9.probes.catalog -> anden9.domain.budget (l.7)
```

Reverted immediately; `httpx` was installed only inside the venv for the observation and then
uninstalled, so it is not a declared dependency.

### A 30 s interval breaks the request budget

`live-map` set to `interval_s=30`, then:

```
FAIL request budget: live-map: 30s is below the 60s floor
FAILED tests/test_budget.py::test_real_catalog_matches_the_budget_of_the_brief
1 failed, 5 passed
```

Reverted to 60 s: the budget reads 116 again and the suite is green.

### Not verified here

- `make check` itself: GNU `make` is not installed on this Windows host. The target is one line
  that runs `scripts/check.py`, which is what was verified; CI runs the real `make check` on
  Ubuntu and the runner on Windows.
- The GitHub Actions workflow: the repository has no remote yet, so it has never run.
- Playwright: green. `pnpm e2e` runs 2 tests (desktop 1440 and mobile 390) against a built
  preview on `127.0.0.1:4319`, both assert the unofficial notice and fail on any console error;
  `pnpm e2e:evidence` wrote `web/.evidence/evidence/shell.png`. The preview needs an explicit
  `--host 127.0.0.1` and a port that is not 4173 on this machine, which is now the config. It is
  not part of `make check` on purpose: the browser suite runs in its own CI job.
- Deployment, systemd and Netlify: M5, owned by Albert.
