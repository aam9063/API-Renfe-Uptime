# Probes

What is measured, how often, and what counts as a valid answer. The catalog is the source of
truth: `prober/src/anden9/probes/catalog.py`. This file explains it, and records what has been
confirmed by observation rather than by assumption.

## Rules that apply to every probe

- One request per run, with the timeout of its catalog entry. No retry inside a check: two
  consecutive failures are what opens an incident.
- The User-Agent is `anden9-probe/<version> (+<site>/metodologia)`. No browser identity.
- One in-flight request per host, never below 60 s per probe, never below 900 s for a heavy probe.
- Under 150 requests per hour to Renfe in total, enforced by `scripts/request_budget.py`.
- A 403, a 429, a protection page or a waiting room is `blocked`, never `down`, and is never
  retried with other headers, another IP or a headless browser.
- `Retry-After` pauses the probe (capped at one hour) and the gap is archived as `blocked`.

## Catalog

Budget of this catalog: 116 requests per hour (the control endpoint is counted apart).

| Probe | Service | Request | Every | Timeout | Degraded over | Valid when |
| --- | --- | --- | --- | --- | --- | --- |
| `nsv-config` | New shop web configuration | GET `https://venta.rsv.renfe.com/config/arch-config.json` | 5 min | 10 s | 3 s | 200 and JSON with `arch.security.apiKey` as a string |
| `nsv-token` | Public token | GET `https://api.rsv.renfe.com/user/external-users-login/v1/tokens/public` with `x-api-key` from `nsv-config` and `channel: VLP` | 5 min | 10 s | 3 s | 200 and an `accessToken` shaped like a JWT |
| `nsv-stations` | Station catalog | GET `https://api.rsv.renfe.com/catalog/masterdata/v1/stations` with the anonymous session headers | 15 min | 10 s | 3 s | 200 and a non-empty list |
| `nsv-search` | Journey search | POST `https://api.rsv.renfe.com/browsing/traveloptions/v1/search-travel`, fixed Madrid to Barcelona route | 15 min | 15 s | 5 s | 200 and a journeys list, possibly empty when that date has no trains |
| `legacy-shop` | Classic shop | GET `https://venta.renfe.com/vol/buscarTren.do?Idioma=es&Pais=ES` plus the DWR `__System.generateId.dwr` call | 15 min | 15 s | 6 s | 200 on both and `handleCallback` with a session id |
| `live-map` | Live long distance fleet | GET `https://tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json` | 1 min | 10 s | 2 s, and empty between 07:00 and 23:00 Madrid | 200 and the JSON shape of the map |
| `gtfs-avld` | AV and LD schedules | conditional GET `https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip` with `If-None-Match` | 15 min | 20 s | 5 s until headers | 200 or 304 |
| `www-search` | renfe.com ticket search | GET `https://www.renfe.com/es/es/buscador-billetes` | 5 min | 10 s | 3 s | 200 and the search page HTML |
| `control` | Control endpoint | GET `https://www.google.com/generate_204` | 5 min, and right after a probe fails | 10 s | 3 s | 204 |

## Why the live map is probed every minute

The author of `renfe-cli` observed the live map refusing connections from Spain for more than
two hours on 17 November, and on 18 November, polling every 15 minutes, cutting out once for
less than a minute. At 15 minutes that short outage would be invisible, and the map answers
with `Cache-Control: max-age=30`, so one request per minute already costs nothing extra.

## What the first real run showed (2026-11-24)

| Probe | Answer | Reading |
| --- | --- | --- |
| `nsv-config` | 200 | the API key is published where the brief says |
| `nsv-token` | 200, JWT | the key plus `channel: VLP` is enough |
| `nsv-stations` | 200, non-empty list | the anonymous session headers we send work |
| `nsv-search` | 401 | the API key alone is not enough: it needs the Bearer token too |
| `legacy-shop` | 200 and 200 | the search page and the DWR call answer |
| `live-map` | 200 with units | the shape of the brief holds |
| `gtfs-avld` | 200, zip | no `ETag` seen yet on the first call |
| `www-search` | 200 with the page | marker found |

The 401 of `nsv-search` was published as `unknown`, not `down`, which is the whole point of the
4xx rule: our request was incomplete, so we had no evidence about Renfe.

## Pending confirmations (M2)

Each of these is closed by observation, with the command and its output recorded in the M2
feature document. None of them is assumed:

1. Where the prober runs, and whether Renfe answers the same from a datacenter IP.
2. Which headers the anonymous session of the new shop requires, and how long the token lasts.
3. Whether `search-travel` answers for dates before 25 January 2027, and which fixed date to use.
4. The shortest classic shop sequence that proves the search works without a full search.
5. During which night hours the live map is legitimately empty.
6. Whether `ssl.renfe.com` returns an `ETag` and answers 304; if not, `HEAD` or `Range`.

Endpoint knowledge comes from `renfe-cli` by Luis González (MIT). Read it from a clone outside
this repository before implementing each probe, and record what changed there.

## What is confirmed and what is not

`probe once --all` is the only thing that answers this, and the answer is in the M2 feature
document. Two probes measure transport availability only until their request body is confirmed:
`nsv-search` and `legacy-shop`. The rest check the shape the brief describes.

An unexpected 4xx that is not 403 or 429 becomes `unknown` with reason `probe_error`: it usually
means our request was wrong, so it is not evidence about Renfe. 404 and 410 stay `down`, because a
vanished endpoint is a real failure.
