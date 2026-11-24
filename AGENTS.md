# AGENTS.md

> Operating manual for AI agents working on **Andén 9**: an unofficial status page that measures the uptime of Renfe's APIs with SaaS standards and reports it as a number of nines.
> Methodology: verification-first (adapted from Lauren Tan's agent workflow: feature maps, hard constraints over soft rules, self-correcting loops, evals for skills) combined with **ODD (Organic Driven Development)** from gentle-ai / gentle-shell and **RDD (Receipt-Driven Development)** review.
> Read `BRIEF.md` for what to build and in which order. This file holds the permanent operating rules.
> Language: code, identifiers, commits, PRs and issues in English. Web copy in Spanish, without em dashes. Report to Albert in Spanish.

---

## 0. Core principle: verify, don't guess

You are a capable engineer with **zero business context** who joined five seconds ago. Your output is only trusted when it is **verified by actually running the software**, the same way a real user would use it.

- **Never** state a root cause ("found the smoking gun") without evidence from code you actually read **and** behavior you actually observed.
- **Never** hand verification back to the human. The human is not your test runner. If you cannot verify something (for example, a production deploy), say so explicitly and explain what is missing.
- Correct code is the minimum bar. Good code is enforced by the constraints in section 5.
- This project publishes claims about a third party. A wrong number is worse than no number: when the data is unclear, the right outcome is `unknown`, never a guess.

---

## 1. The agent loop (mandatory for every task)

Run this loop autonomously. Do not stop and ask the human unless you are blocked by something only a human can provide (credentials, a VPS, a product decision, a legal question, an irreversible action).

```
1. UNDERSTAND   → Restate the task. Map it to a feature using the Feature Map (section 3).
2. REPRODUCE    → For bugs: reproduce it (recorded HTTP fixture, local stack or a one-shot probe) BEFORE touching code.
                  For features: define how you will verify it works (acceptance check).
3. INVESTIGATE  → Read the code that is actually involved. Use sub-agents to search in parallel.
                  Form hypotheses, then confirm each one with evidence (logs, traces, tests).
4. IMPLEMENT    → Follow existing conventions. The shortest path must be the correct path (section 5).
5. VERIFY       → Run the app with the verification skill (section 2). Observe the real behavior.
                  Run static checks: make check (typecheck, lint, test, arch for prober and web).
6. SELF-CORRECT → If anything fails, go back to step 3 with the new evidence. Repeat.
                  Do not exit the loop until verification and all checks are green.
7. DELIVER      → Split into atomic PRs (section 6). Report what you verified and how.
8. LEARN        → If you hit a failure mode that a rule could have prevented, propose a new
                  lint / CI check / skill (section 5.3).
```

### 1.1 How the loop maps to ODD

ODD runs on every implementation request. The loop above is the detailed form of ODD steps 2 to 7.

| ODD step | Loop step | What it means here |
|---|---|---|
| 1. Authorize | before 1 | Questions, reviews and proposals are **read-only**. Change files only when Albert asks for a change |
| 2. Explore | 1, 3 | Read the affected code and docs. For a probe, also read the matching file of `renfe-cli` (outside the repo) |
| 3. Resolve uncertainty | 3 | Close open questions by investigating or observing (list in `BRIEF.md` section 9.1), never by assuming |
| 4. Classify | 1 | **Small**: understood, localized change. **Substantial**: several features, a new contract, a migration, or a high-risk area (section 6.1) |
| 5. Track | 4 | Substantial work only: one feature document under `odd/` with tasks and status, so work can resume across sessions |
| 6. Implement | 4 | Task by task, copying the canonical pattern (section 5.2) |
| 7. Close | 5 to 7 | Close with verified proof: the evidence listed in the exit criteria below |

Small work stays light: no feature document, no planning pipeline. Do not turn a copy fix into ceremony.

### Loop exit criteria (all must be true)

- [ ] The bug no longer reproduces / the feature behaves as specified **in the running app or with a real probe run**.
- [ ] Evidence is attached: test output, `anden9 probe once` output, Playwright screenshots, SQL query results, or numbers before/after.
- [ ] `make check` passes locally (prober: `uv run mypy`, `uv run ruff check`, `uv run pytest`, `uv run lint-imports`; web: `pnpm typecheck`, `pnpm lint`, `pnpm test`, `pnpm arch`; plus `scripts/repo-hygiene` and `scripts/request-budget`).
- [ ] No new violations of the hard constraints (section 5.1).
- [ ] No performance regression on the affected path (section 4).
- [ ] Anything that could not be verified is listed explicitly as **not verified**, with the reason.

### Special case: "already fixed?"

When reproducing a bug report, first check it against the latest `dev`. If it does not reproduce on `dev`, report: *"Reproduced on <commit or tag>, already fixed on `dev`, needs promotion to `main` by Albert."* Do not write code.

### Special case: "Renfe changed something"

If a probe starts returning `bad_shape`, first compare the live response with the recorded fixture and check recent commits of `renfe-cli`. Report observed facts before changing the parser, and never relax validation just to turn a probe green.

---

## 2. Verification skill

The agent must be able to operate the application like a user and inspect it like an engineer. There are two apps: the **prober** (a Python service with a CLI) and the **web** (a React SPA).

| Capability | How in this project |
|---|---|
| Launch a dev build | `supabase start` (local Postgres + API), then `uv run anden9 run --catalog dev` in `prober/` (reduced catalog: `live-map` and `www-search`), then `pnpm dev` in `web/` |
| Programmatic UI control | Playwright: `pnpm e2e` (headless), `pnpm e2e --ui` for debugging. Viewports 1440 and 390 |
| Screenshots | `pnpm e2e --project=evidence` saves full-page captures to `web/.evidence/<task>/`, attached to the PR |
| Console / logs | Prober: JSON lines on stdout, `uv run anden9 logs` pretty-prints them. Web: Playwright collects console errors and fails the test on any `error` |
| CPU / performance traces | Prober: `uv run python -X importtime` and `py-spy` only when a slowdown is suspected. Web: Playwright trace (`--trace on`) and Lighthouse CI on the built site |
| Heap snapshots / memory | Prober: `tracemalloc` snapshot via `uv run anden9 debug memory` when a leak is suspected (the scheduler runs for weeks). Web: Chrome DevTools Memory tab through Playwright if needed |
| Network inspection | Prober: `uv run anden9 probe once <id> --verbose` prints request line, status, headers subset and timings (never the Renfe key or token). Web: Playwright `page.on('request')` |
| API / backend checks | `uv run anden9 probe once --all` against real Renfe (limits in section 2.1). SQL against local Supabase: `supabase db query` or `psql` on the local URL |
| Test data / seed | `supabase db reset` loads `supabase/seed/`. Recorded HTTP fixtures in `prober/tests/fixtures/http/` |
| Test credentials | Local Supabase keys from `supabase status`. Production keys exist only on Albert's VPS and in Netlify; agents never see them |

Rules:
- Verification is done against the **real running software**, not by reading code and assuming.
- When analyzing latency or a profile, cite the concrete number or function you found, not a vague impression.
- If the verification tooling itself is broken, fixing it has priority over the original task, and you must say so.

### 2.1 Talking to the real Renfe

- `anden9 probe once` against real Renfe: **at most once every 5 minutes per agent session, never in a loop**, and never as part of the default test suite. Paste the output in the PR.
- The real scheduler (`anden9 run` with the full catalog) is only run by Albert, on the VPS.
- If a probe gets `blocked`, stop calling that endpoint for the rest of the session and report it. Never retry with different headers, a browser user agent, another IP or a headless browser.
- Never download or commit Renfe data files. Read `renfe-cli` from a clone outside the repo; do not run it from your session.

---

## 3. Feature Map

The Feature Map lives at `docs/feature-map.md`. It teaches you **where every feature is and how to reach it**, so vague reports ("the 30d number looks wrong", a screenshot with "???") can be mapped to code and to a reproduction path.

### Format for each entry

```markdown
## <feature-name>
- What it is (user point of view): <one line>
- Sub-features: <list>
- How to reach it in the UI: <route and navigation steps, or CLI command for prober features>
- Keyboard shortcuts: <none unless added>
- Selectors for programmatic control: <data-testid values>
- Code location: <feature directory>
- Backend/API involved: <Supabase views, tables, Renfe endpoints>
- Known pitfalls: <notes>
```

### Maintenance

- **Creating it:** milestone M0 creates the initial map from `BRIEF.md` section 8. Extend it entry by entry as features land.
- **Maintaining it:** any PR that adds, moves, renames or removes a feature, route, probe, view, config key or `data-testid` **must update the Feature Map in the same PR**. Probe changes also update `docs/probes.md`.
- If you could not find a feature quickly using the map, that is a defect in the map: fix it.

---

## 4. Investigation discipline (anti-hallucination)

- Read the files that are actually affected before proposing a cause. Check your own tool calls: if you did not open the relevant code, you do not know the answer yet.
- Use sub-agents for wide searches (call sites, related features, history) and keep the main agent as coordinator.
- Use `git log` / `git blame` on the affected files: the git history is a primary source of context.
- Separate clearly in your report: **observed facts**, **hypotheses**, **confirmed causes**.
- Third-party behavior (Renfe endpoints, headers, response shapes, Supabase limits, library APIs) must be confirmed against current sources or by observation. Do not rely on memory of an older version.
- When a number on the page looks wrong, recompute it by hand from `checks` with SQL before touching any view, and show both results.
- Performance targets. Prober: the scheduler loop never blocks for more than ~50 ms; every probe call is async with its own timeout; memory stays flat over 24 h. Web on `React 19`: target 60 fps, every frame must finish in ~16 ms; the 90-day bars (up to 8 × 90 elements) render without long tasks over 50 ms; Lighthouse performance ≥ 90 on mobile for the home page.

---

## 5. Constraints: hard beats soft

Enforcement layers, from strongest to weakest:

1. **Codebase architecture and conventions** (strongest: agents copy existing patterns)
2. **Static analysis**: compiler/type checker, lints, CI checks, dependency-graph checks
3. Rules files (this file)
4. Skills
5. Review: native RDD (section 6.1); there is no external code-review bot

Layers 1 and 2 make CI **red**. Layers 3 to 5 are soft: agents can forget them. Never rely only on soft layers for anything important.

### 5.1 Hard constraints (enforced by CI in this project)

| Constraint | Enforced by |
|---|---|
| Each feature is colocated in one directory: `web/src/features/<feature-name>/` with a public `index.ts`; each probe is one file in `prober/src/anden9/probes/<id>.py` registered in `catalog.py`. No deep imports into another feature | `pnpm arch` (dependency-cruiser), `uv run lint-imports` |
| Layer boundaries: `prober/src/anden9/domain/` is pure (no `httpx`, no `supabase`, no `datetime.now`, no `os.environ`). Adapters implement the domain ports. In the web, only `web/src/data/` imports the Supabase client, and the web only reads views (`v_*`), never tables | `uv run lint-imports` (import-linter contracts), `pnpm arch`, ESLint `no-restricted-imports` + a test that greps queries for `from('v_` |
| Uptime and nines are computed in one place: the SQL views. The web only formats (`web/src/lib/format.ts`). `contracts/uptime_cases.json` runs against the views and against the formatter | contract tests in `pytest` (local Supabase) and `vitest` |
| `blocked` and `unknown` never lower uptime; 2 consecutive failures open an incident and 2 successes close it; percentages are truncated, not rounded | property tests (hypothesis) + contract cases |
| Politeness: no probe interval below 60 s; heavy probes (`nsv-stations`, `nsv-search`, `legacy-shop`, `gtfs-avld`) not below 900 s; one in-flight request per host; total budget under 150 requests/hour to Renfe hosts | `scripts/request-budget` (reads the catalog) + scheduler tests |
| Honest identity: the User-Agent is the constant `anden9-probe/<version> (+<site>/metodologia)`; no `Mozilla`, no browser fingerprints. Banned dependencies in `prober/`: `playwright`, `selenium`, `undetected-chromedriver`, `cloudscraper`, `curl_cffi`, any captcha solver or proxy-rotation package | test on the HTTP adapter + `scripts/repo-hygiene` (dependency denylist) |
| No retries inside a check; a 403, 429, challenge or waiting-room page is `blocked`, never `down`, and is never retried; `Retry-After` pauses the probe (capped at 1 h) | classifier and scheduler tests with recorded fixtures |
| Renfe's public API key and anonymous token live only in memory: never logged, never stored, never sent to Supabase | "canary" test (a unique fake key injected through the pipeline must not appear in logs, DB writes or exceptions) |
| Supabase `service_role` key is only read by `prober/src/anden9/config.py`; the web bundle only contains the anon key; RLS lets `anon` select views and nothing else | `scripts/repo-hygiene` (greps the built bundle for `service_role`) + RLS test in `pytest` against local Supabase |
| Secrets are never versioned: `.env*`, `supabase/.temp/`, `*.pem`, `*.key` are in `.gitignore` and no tracked file matches them | `scripts/repo-hygiene` |
| The web shows the "No oficial · sin relación con Renfe" notice on every route, and the repo contains no Renfe logos or brand assets | Playwright test over every route + `scripts/repo-hygiene` (file name and image hash denylist) |
| Web copy in Spanish without em dashes (U+2014) | `scripts/repo-hygiene` over `web/src/` and `docs/` |
| React 19 data access goes through TanStack Query hooks in `web/src/data/`; `useEffect` is banned in feature code | ESLint (`no-restricted-syntax` / `no-restricted-imports`) |
| Accessibility: no serious or critical axe violations; interactive elements are real `button`/`a`/`input` | Playwright + `@axe-core/playwright` |
| No code comments that narrate history, chat instructions or decisions ("Albert said never do this"). Code must be self-explanatory; context goes in the PR description. Allowed exceptions: docstrings/TSDoc on public symbols, and a short `WHY:` comment stating a non-obvious fact about Renfe's behavior in the present tense, with the date it was observed | ruff and ESLint reject `TODO/FIXME/HACK` without an issue id; the rest is checked by the RDD readability lens |
| Strict typing, no escape hatches: mypy `--strict`, no `Any`, no `type: ignore` without an error code; TS `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, no `any`, no `@ts-ignore` | `uv run mypy`, `pnpm typecheck`, ruff, ESLint |
| Thresholds, intervals and timeouts are catalog values, never magic numbers in logic | ruff `PLR2004` on `prober/src/`, ESLint `no-magic-numbers` on `web/src/features/` |
| New runtime dependencies need an explicit justification in the PR | RDD risk lens + review |

### 5.2 Conventions ("the shortest path is the best path")

- Agents naturally take shortcuts, so the framework is designed so that **the quickest way to solve a problem is the correct way**.
- To create a new probe, copy `prober/src/anden9/probes/_template.py` (it already has the timeout, the classifier call, the fixture-based test and the catalog entry). To create a new web feature, copy `web/src/features/_template/`. To add a public aggregate, copy an existing `v_*` view migration and add contract cases. Do not invent a new structure.
- ~80% of work on a feature should stay inside its own directory. If you need to touch many unrelated places, stop and reconsider the design.
- Anything that talks to the outside world (Renfe, Supabase, the clock) sits behind a port with a fake, so tests run with no network.

### 5.3 Turning feedback into rules

Every time a human has to write a review comment saying "don't do this", that is a **smell**. Instead of only fixing the PR:

1. Fix the PR.
2. Propose how to make it impossible next time, in this order of preference:
   - eliminate the problem categorically (architecture/API change),
   - add a lint rule or CI check,
   - add a compiler/type-level constraint,
   - only as a last resort, add a line to this file or a skill.
3. Do **not** turn one-off review feedback into a global rule unless Albert confirms it is durable.

---

## 6. Pull requests and Git flow

```
main  <- Albert merges by hand
 dev  <- Albert merges by hand (every PR)
  feat/<slug>   fix/<slug>   chore/<slug>   <- agents work here, branching from dev
```

- Split work into **multiple atomic PRs**; each PR describes one small, coherent change. No hard size cap, but a reviewer must be able to understand and revert it in isolation.
- Branch naming: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, always created from `dev`. Commit message format: Conventional Commits with the area as scope (`feat(probes): add live-map probe`, `fix(views): truncate uptime instead of rounding`).
- Agents commit, push their branch and open a PR **against `dev`**. Agents never push to `main` or `dev`, never force-push shared branches, and **never merge anything**.
- A migration goes in its own PR, never mixed with UI work.
- PR description must contain:
  - **What & why** (link to the GitHub issue, `#<n>`)
  - **How it was verified** (commands run, probe output, screenshots, SQL results, before/after numbers) and what was **not verified**
  - **Feature Map updated?** yes / not needed (and `docs/probes.md` for probe changes)
  - **New constraint proposed?** (if section 5.3 applied)
  - **RDD:** on / off, and the review outcome when on
- Auto-merge policy: **disabled**. Albert merges every PR into `dev` and promotes `dev` to `main` himself. Review happens before merge, by Albert and by RDD when it is on.

### 6.1 RDD (Receipt-Driven Development)

RDD is gentle-ai's native, bounded review. In current gentle-ai it is **on by default** and turned off with `gentle-ai review mode disable`. The switch is **owned by Albert**: agents never enable or disable it.

- At the start of a task, run `gentle-ai review mode status --cwd .` and report the effective mode. If it is off, continue with ODD and write `RDD: off` in the PR.
- When it is on, after each work-unit commit assess the exact change (native risk assessment, `assess` operation, from the last reviewed boundary, committed changes only). The assessment is read-only and picks the depth: passive (structural readback, no reviewer lenses), medium (one focused lens), high (the four lenses). At most one bounded correction is allowed, and one exact acknowledgement closes the transaction. **Delivery stays human-owned.**
- The four lenses: **Risk** (credibility of published data, secrets, permissions, contracts), **Resilience** (network failures, gaps, restarts, back-off), **Readability** (API, messages, copy, documentation), **Reliability** (logic the tests must pin down, above all the uptime math).

Risk map of this project (a change touching any high item gets an independent verifier, whichever model wrote it):

| Level | Areas |
|---|---|
| High | `scheduler` (intervals, budget, `Retry-After`), User-Agent and request headers, `classifier`, `incident-tracker`, SQL views with the formula, migrations and RLS, secret handling (`service_role`, Renfe key and token) |
| Medium | Parsers of each probe, `web/src/data/`, number and duration formatting |
| Passive | Styles, copy, docs, tests, behavior-preserving refactors |

---

## 7. Skills and how they are maintained

Skills live in `.agents/skills/`. Reuse the curated skills that gentle-ai already installed before writing new ones. Each skill encodes a lesson learned from an **observed failure mode** of agents. Expected first skills for this project: "add a probe from renfe-cli", "recompute uptime by hand with SQL", "drive the web with Playwright and attach evidence".

### Eval playbook (run every time a skill is created or modified)

1. **Coordinator agent** writes a rubric of what the skill must achieve.
2. Coordinator spawns **N sub-agents**, each in its own directory with **neutral names** (sub-agents must not realize they are being evaluated, since that changes their behavior).
3. Each sub-agent performs a realistic task using the skill, against recorded fixtures (never against real Renfe).
4. Coordinator scores every run against the rubric (e.g. 0 to 10).
5. A **judge agent on a different model** cross-checks the scores to remove self-bias.
6. Run across the models Albert actually uses: the ones configured in the active gentle-shell profiles (read them from `/gentle:status`, do not hardcode them).
7. **Hill-climb**: loop (modify skill → re-run eval) until the target score is reached (e.g. 10/10 on every rubric item) or progress stalls; then report.

Store evals in `evals/`.

---

## 8. Local first, then cloud and automations

- New verification skills are built and observed **locally** first: watch how the agent drives the CLI, the local stack and Playwright, and fix where it gets lost.
- Cloud agents: none for v1. Agents work in Albert's local gentle-shell sessions.
- Automations built on the same verification:
  - **CI** (GitHub Actions) on every PR to `dev`: `make check` + Playwright against seeded local Supabase. Never calls real Renfe.
  - **Heartbeat watchdog**: a scheduled workflow that reads `heartbeat` through the public view and opens a GitHub issue if the prober has been silent for more than 10 minutes.
  - **Probe drift report** (later, with Albert's approval): a weekly job that summarizes `bad_shape` and `blocked` counts per probe, so parser drift is noticed early.

Scale gradually: do not jump from 1 trusted agent to many parallel agents; untrusted parallelism only burns tokens. Parallel writers only for units with disjoint edit surfaces (for example, two different probes, or prober and web).

---

## 9. Project reference

- Stack: prober in Python 3.14 (`uv`, `httpx`, `pydantic-settings`, pytest, respx, hypothesis, ruff, mypy, import-linter); Supabase Postgres (migrations, RLS, views); web in React 19 + TypeScript + Vite + Tailwind CSS + pnpm (TanStack Query, `@supabase/supabase-js`, Vitest, Playwright, `@axe-core/playwright`, ESLint, dependency-cruiser).
- Repo layout: `prober/` (`src/anden9/domain`, `probes`, `adapters`, `scheduler.py`, `cli.py`, `config.py`), `web/` (`src/features`, `src/data`, `src/ui`, `src/lib`, `e2e/`), `supabase/` (`migrations/`, `seed/`), `contracts/`, `docs/`, `odd/`, `evals/`, `scripts/`.
- Environments: (1) **test**: fixtures and fakes, no network; (2) **local**: Supabase local + prober with the dev catalog + web dev server; (3) **one-shot real**: `anden9 probe once` against Renfe under section 2.1; (4) **production**: prober on Albert's VPS (region to be confirmed), Supabase cloud project, web on Netlify. Only Albert touches production.
- Design reference: the "Nueves: status page de las APIs de Renfe" canvas linked in `BRIEF.md` (home desktop, service detail, methodology, home mobile). Its numbers are sample data.
- Endpoint reference: `renfe-cli` by Luis González (MIT), read from a clone outside the repo. Credit it in the methodology page and in `NOTICE` if any logic is ported.
- Domain glossary: `docs/glossary.md` (uptime, nines, SLA, SLO, probe, check, outcome, reason, control endpoint, incident, heartbeat, window, venta nueva / NSV, venta clásica, DWR, GTFS, ETag, RLS, ODD, RDD).
- Owners / escalation: Albert is the only owner and the escalation point for every decision, including anything legal or reputational about Renfe.
- Things you must never do:
  - run the full scheduler against real Renfe, call Renfe in a loop, or exceed the request budget;
  - try to get past a block: no browser user agents, headless browsers, proxies, IP rotation, captcha solving or waiting-room tricks;
  - buy, reserve or start a payment on any Renfe system, even as a guest;
  - log, store or commit Renfe's API key or tokens, the Supabase `service_role` key, or any `.env` file;
  - publish or change a number on the page without a test that pins the math behind it;
  - present the site as official, or add Renfe logos or brand assets;
  - write migrations that drop or rewrite `checks` or `incidents` data without Albert's explicit approval;
  - deploy to production, touch the VPS, Netlify or the Supabase cloud project;
  - enable or disable RDD, merge any PR, push to `main` or `dev`, or force-push any shared branch;
  - add a dependency without justifying it in the PR.
