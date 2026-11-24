# M1: measurement domain without network

Feature document for milestone M1 of `BRIEF.md` section 12. Substantial work: the rules that decide
what a number means, with no network, no database and no real clock.

## Specs

S1 (scope, verbatim from `BRIEF.md` §12):

> - `Outcome`, `classifier`, `incident-tracker`, cobertura de intervalos y huecos.
> - `contracts/uptime_cases.json` con casos de referencia (sin caídas, todo bloqueado, ventana insuficiente, truncado de 99,996 %, 1 a 5 nueves).

S2 (acceptance, verbatim):

> **Aceptación:** tests con hypothesis para las propiedades (el uptime nunca sale de [0, 1], bloqueado y sin datos nunca bajan el uptime, 2 fallos abren y 2 éxitos cierran). Todos los casos del contrato pasan.

S3 (measurement rules, verbatim from `BRIEF.md` §5.2):

> - Cada comprobación cubre el intervalo desde su inicio hasta la siguiente, con un máximo de 2 veces su intervalo nominal. Lo que quede sin cubrir es `unknown` con reason `gap`.
> - `uptime = (s_up + s_degraded) / (s_total - s_blocked - s_unknown)`, en segundos enteros.
> - `nueves = floor(-log10(1 - uptime))`. Si no hubo ningún segundo caído, no hay nueves que calcular: se muestra "sin caídas" (nunca "infinitos nueves").
> - Si el denominador es menor que el 50 % de la ventana, la ventana se marca como "datos insuficientes" y no se muestran nueves.
> - Los porcentajes se **truncan** (no se redondean) a dos decimales, para que 99,996 % se vea como 99,99 % y no como 100,00 %.

S4 (states, verbatim from `BRIEF.md` §5.1): `up` and `degraded` count as available, `down` counts
against, `blocked` and `unknown` are excluded from the denominator.

S5 (incidents, verbatim from `BRIEF.md` §5.3):

> - Se abren tras **2 comprobaciones `down` seguidas** de la misma sonda (o 2 `degraded`, o 2 `blocked`, cada tipo por separado) y se cierran tras **2 `up` seguidas**. La duración cuenta desde el primer fallo.

S6 (freshness rule of `BRIEF.md` §6): the live map answering empty outside its night window is
`degraded`, an empty answer inside the night window is normal.

## Tasks

| ID | Task | Specs | Route | Commit |
| --- | --- | --- | --- | --- |
| T1 | Extend the classifier with payload states, bot page detection and the control endpoint gate | S1, S4, S6 | inline | `feat(domain): classify payload states, bot pages and control failures` |
| T2 | Interval coverage: every check covers up to the next one or twice its interval, the rest is a gap | S1, S3 | inline | `feat(domain): cover check intervals and report gaps` |
| T3 | Uptime and nines as an executable specification, with truncation and insufficient windows | S1, S3 | inline | `feat(domain): compute uptime, nines and truncation` |
| T4 | Incident state machine per probe and kind | S1, S5 | inline | `feat(domain): open and close incidents after two consecutive checks` |
| T5 | Shared contract cases and the tests that run them on both sides | S1, S2 | inline | `feat(contracts): add the uptime cases` |
| T6 | Property tests with hypothesis for the four properties of the acceptance | S2 | inline | `test(domain): pin the uptime properties with hypothesis` |

## Log

### L1 (original request, verbatim)

> ok continua y no pares hasta tenerlo todo terminado. No preguntes a no ser que sea necesario. Y
> RDD tambein permitido. No pares

### L2 (decisions)

- **The SQL views stay the runtime truth.** `domain/uptime.py` is the executable specification the
  property tests quantify over and that the contract cases run against. M3 makes the views
  reproduce the same contract file; if they ever disagree, the views win and this module is fixed,
  never the other way round.
- **Probes declare payload quality, the classifier decides.** A probe answers `VALID`, `EMPTY` or
  `INVALID`; the classifier maps that plus the status code to an outcome, so no probe can publish a
  state by itself.
- **Bot page detection only ever improves the fairness.** It looks for markers of a protection
  page and can only turn a would-be `down` into `blocked`, which never lowers the published
  uptime. The marker list is a heuristic and is recorded as such; M2 refines it with what a real
  answer looks like.
- **Exact arithmetic.** Uptime is a `Fraction`, never a float, so the truncation and the nines of
  the contract cases are exact.
