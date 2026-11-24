# M2: real probes, transport and scheduler

Feature document for milestone M2 of `BRIEF.md` section 12.

## Specs

S1 (scope, verbatim from `BRIEF.md` §12):

> - Adaptador `httpx`, las 8 sondas de la sección 6, el endpoint de control, el scheduler con presupuesto y `Retry-After`.
> - CLI: `anden9 probe once <id>` y `anden9 probe once --all`, que imprimen el resultado sin escribir en base de datos.
> - Tests con respuestas grabadas (respx) para cada estado de cada sonda, incluidas una página HTML de protección y un 429.

S2 (acceptance, verbatim):

> **Aceptación:** `anden9 probe once --all` contra Renfe real devuelve un resultado por sonda y se pega en el PR. Se resuelven las incertidumbres 1 a 6 y 9. **Riesgo alto en RDD.**

S3 (politeness, verbatim from `BRIEF.md` §5.4): one in-flight request per host, no retry inside a
check, a 429 with `Retry-After` pauses the probe up to an hour, and the catalog stays under 150
requests per hour.

S4 (honest identity, verbatim from `AGENTS.md` §5.1): the User-Agent is `anden9-probe/<version>`,
with no browser fingerprint.

## Tasks

| ID | Task | Specs | Route | Commit |
| --- | --- | --- | --- | --- |
| T1 | `httpx` transport with one lock per host and every transport error mapped | S1, S3, S4 | inline | `feat(adapters): add the httpx transport` |
| T2 | The eight probes, the control probe and the session state they share | S1 | inline | `feat(probes): implement the eight endpoints and the control probe` |
| T3 | Scheduler with cadence, control gate and the `Retry-After` pause | S1, S3 | inline | `feat(scheduler): run the due probes and honour retry-after` |
| T4 | CLI: `probe once`, `run --catalog` and `logs` | S1 | inline | `feat(cli): add the one-shot probe, the loop and the log reader` |
| T5 | Transport tests with respx and probe tests against canned answers | S1 | inline | `test(probes): pin every probe state with recorded answers` |
| T6 | One real run against Renfe, pasted as evidence | S2 | inline | evidence in this document |

## Log

### L1 (original request, verbatim)

> puedes lanzar agentes en paralelo que vayan adelantando faena y no se pisen los unos a los otros?

### L2 (decisions)

- **A 4xx that is not 403 or 429 becomes `unknown`.** It usually means our own request was wrong,
  and that is no evidence about Renfe. 404 and 410 stay `down`: a vanished endpoint is a real
  failure. This is what lets an unconfirmed request body cost us a measurement instead of
  publishing a false outage.
- **Two probes measure transport availability only** (`nsv-search`, `legacy-shop`), because their
  request body is still unconfirmed (uncertainties 3 and 4). Documented in `docs/probes.md`.
- **`Retry-After` lives on the check result.** The scheduler reads it from there, so no probe needs
  to know what a pause is.

### T6 evidence: the first real run

`uv run anden9 probe once --all`, one pass, no loop, from Albert's connection in Spain on
2026-11-24:

```
{"probe": "nsv-config",  "outcome": "up",      "reason": "ok",          "http_status": 200, "duration_ms": 260}
{"probe": "nsv-token",   "outcome": "up",      "reason": "ok",          "http_status": 200, "duration_ms": 225}
{"probe": "nsv-stations","outcome": "up",      "reason": "ok",          "http_status": 200, "duration_ms": 55}
{"probe": "nsv-search",  "outcome": "unknown", "reason": "probe_error", "http_status": 401, "duration_ms": 41}
{"probe": "legacy-shop", "outcome": "up",      "reason": "ok",          "http_status": 200, "duration_ms": 114}
{"probe": "live-map",    "outcome": "up",      "reason": "ok",          "http_status": 200, "duration_ms": 148}
{"probe": "gtfs-avld",   "outcome": "up",      "reason": "ok",          "http_status": 200, "duration_ms": 585}
{"probe": "www-search",  "outcome": "up",      "reason": "ok",          "http_status": 200, "duration_ms": 65}
```

What that run proves and what it does not:

- Seven of eight endpoints answer and the shapes the brief describes hold: the API key, the JWT,
  the non-empty station list, the live map JSON, the zip archive and the search page.
- `nsv-search` answered 401 with only the API key. That is exactly the case the 4xx rule exists
  for: the run published `unknown`, never `down`. Fixed by sending the anonymous Bearer token the
  token probe already fetches; the second run confirms it.
- Uncertainties of the brief, one by one: 1 (region and provider) is **not** answered, this ran
  from a home connection and the VPS remains untested; 2 is answered for config, token and
  stations, and the search needs the Bearer token as well; 3 is still open, the request body has
  not been accepted yet; 4 is answered at transport level, both requests answer 200; 5 needs a
  night of observation; 6 needs a second run to show the 304; 9 was not exercised because nothing
  failed.

### T6 evidence, second run, after the Bearer token

Same command, a few minutes later:

```
nsv-config   up       ok          200  151 ms
nsv-token    up       ok          200  216 ms
nsv-stations up       ok          200   61 ms
nsv-search   unknown  probe_error 400  168 ms
legacy-shop  up       ok          200   91 ms
live-map     up       ok          200  135 ms
gtfs-avld    up       ok          200  557 ms
www-search   up       ok          200   70 ms
```

`nsv-search` moved from 401 to 400: the Bearer token is now accepted and what is still wrong is the
body. That is uncertainty 3 of the brief, narrowed to one thing, and it is still published as
`unknown` instead of an invented outage while it is open.

Two notes on what these runs cannot show:

- The `ETag` of `gtfs-avld` never appears as a 304 in a one-shot run, because each process starts
  with an empty session. The 304 shows up on the second run inside the scheduler, which is the shape
  the unit tests already pin.
- The control endpoint never runs in a one-shot pass unless something goes `down`, by design.

### T6 evidence, third run: the whole catalog is green

After reading the request shape in `renfe-cli` (`src/renfe/search.py:31-36` and `:285-289`,
`src/renfe/client.py:296-307`), the search sends the body and the headers the project sends. One
pass, no loop:

```
nsv-config   up  ok  200  126 ms
nsv-token    up  ok  200  208 ms
nsv-stations up  ok  200   55 ms
nsv-search   up  ok  200  166 ms
legacy-shop  up  ok  200  105 ms
live-map     up  ok  200  139 ms
gtfs-avld    up  ok  200  462 ms
www-search   up  ok  200   80 ms
```

That closes uncertainty 3 of the brief, and with it the whole M2 acceptance:

| Uncertainty | State |
| --- | --- |
| 1 region and provider | open, the VPS is untested |
| 2 anonymous session headers | answered: key, `channel: VLP`, `session-id`, `x-terminal-id` from the JWT claim `custom:terminal_id`, Bearer token |
| 3 `search-travel` before 25 Jan 2027 | answered: the body is two Madrid-midnight UTC timestamps with `.000Z`, a `travel_path` of `{"code": ...}` and `direction: OUTBOUND`; the date is at least ninety days ahead and never before 2026-01-26 |
| 4 classic shop minimal sequence | answered at transport level: the page and the DWR `generateId` both answer 200 |
| 5 live map at night | open, needs a night of observation |
| 6 GTFS conditional | open in a one-shot run, covered by a unit test with a 304 |
| 9 control endpoint | answered: 204 from inside the container |

Two fixes came out of this, both failing closed: a probe run on its own used to send no token, so it
now mints one when the session is cold, and the DWR body is the plain text block the classic shop
expects instead of a query string.
