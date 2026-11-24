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
