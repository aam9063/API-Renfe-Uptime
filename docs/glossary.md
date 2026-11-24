# Glossary

Domain vocabulary, so a report such as "the 30d number looks wrong" maps to one term and one
place in the code. Web copy is Spanish; the identifiers in code are English.

| Term | Meaning here |
| --- | --- |
| **uptime** | Share of measured seconds in which the service was available: `(s_up + s_degraded) / (s_total - s_blocked - s_unknown)`. Computed only in the SQL views. |
| **nines** (`nueves`) | `floor(-log10(1 - uptime))`. 99.9 % is 3 nines. No downtime at all is reported as "sin caídas", never as infinite nines. |
| **SLA** | What a provider promises in a contract. This project promises nothing and measures a third party. |
| **SLO** | An internal target for a service. The nines scale is used as a comparison, not as a commitment. |
| **probe** (`sonda`) | One measured endpoint: a catalog entry plus one module in `prober/src/anden9/probes/`. |
| **check** (`comprobación`) | One execution of a probe, stored as one row with outcome, reason, latency and status. |
| **outcome** (`estado`) | One of `up`, `degraded`, `down`, `blocked`, `unknown`. |
| **reason** (`motivo`) | Stable cause attached to a check: `timeout`, `conn_refused`, `dns`, `tls`, `http_5xx`, `bad_shape`, `slow`, `empty`, `http_403`, `http_429`, `bot_page`, `control_failed`, `probe_error`, `gap`, and `ok` for a healthy check. |
| **control endpoint** | A neutral endpoint probed to prove the network works. A failure there turns a `down` into `unknown`, never into a published outage. |
| **incident** | A stretch of equal failing outcomes: opened after 2 consecutive failures of the same probe, closed after 2 consecutive successes. |
| **heartbeat** | The prober's own sign of life. If it stops, the page says "sin datos" instead of inventing uptime. |
| **window** (`ventana`) | The period an aggregate covers: 24 hours, 7, 30 or 90 days. |
| **rollup** | A daily aggregate kept forever, so raw checks can be pruned after 120 days. |
| **venta nueva / NSV** | Renfe's new ticket-selling system. It sells journeys from 25 January 2027. |
| **venta clásica** | The old `venta.renfe.com` shop, DWR based. Retired when the new one takes over. |
| **DWR** | Direct Web Remoting, the RPC style of the classic shop (`__System.generateId.dwr`). |
| **GTFS** | General Transit Feed Specification, the AV/LD schedule archive served from `ssl.renfe.com`. |
| **ETag** | Validator sent with `If-None-Match` so a 304 answer costs almost nothing. |
| **RLS** | Row Level Security in Supabase. `anon` may select views and nothing else. |
| **ODD** | Organic Driven Development: the working loop described in `AGENTS.md` and `BRIEF.md` section 9. |
| **RDD** | Receipt-Driven Development: gentle-ai's native bounded review, owned by Albert. |
