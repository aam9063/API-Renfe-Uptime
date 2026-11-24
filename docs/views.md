# Public views

The web reads only these. They are the whole contract between the database and the page, so this
file is the reference both sides implement against. `M3` creates them, `M4` consumes them.

Every view is readable by `anon`. No table is. Writes belong to `service_role` and only the prober
holds it.

## `v_status_now`

One row per enabled probe: what the page shows as "now".

| Column | Type | Meaning |
| --- | --- | --- |
| `probe_id` | text | catalog id, for example `live-map` |
| `name` | text | display name |
| `group_name` | text | `venta nueva`, `venta clásica`, `información`, `web` |
| `host` | text | the host that is measured |
| `outcome` | outcome | last known state, `unknown` when it never reported |
| `reason` | text | stable reason of that state, `gap` when it never reported |
| `last_check_at` | timestamptz | null when it never reported |
| `duration_ms` | integer | latency of that last check, null when there is none |

## `v_uptime_windows`

Four rows per probe, one per window. `window_key` is `24h`, `7d`, `30d` or `90d`.

| Column | Type | Meaning |
| --- | --- | --- |
| `probe_id` | text | |
| `window_key` | text | `24h`, `7d`, `30d`, `90d` |
| `window_label` | text | what the page shows next to the number |
| `uptime` | numeric | between 0 and 1, null when the denominator is zero |
| `display_percent` | text | truncated to two decimals with a comma, as the shared contract expects |
| `nines` | integer | null when no second was lost |
| `down_seconds` | bigint | |
| `denominator_seconds` | bigint | up + degraded + down |
| `insufficient` | boolean | denominator under 50 % of the window |
| `no_downtime` | boolean | no second lost |

## `v_daily_90`

One row per probe and day, for the strip of bars.

| Column | Type | Meaning |
| --- | --- | --- |
| `probe_id` | text | |
| `day` | date | Madrid day |
| `worst_outcome` | outcome | down beats degraded beats blocked beats unknown beats up |
| `uptime` | numeric | that day only |
| `display_percent` | text | truncated two decimals with a comma |

## `v_latency_24h`

One row per probe and half-hour bucket, with the two percentiles the page prints.

`probe_id`, `bucket_start` (timestamptz), `p50_ms` (integer), `p95_ms` (integer).

## `v_recent_checks`

The last fifty checks of each probe: `probe_id`, `started_at`, `outcome`, `http_status`,
`duration_ms`. No reason: it is internal vocabulary, and the page explains states in prose.

## `v_incidents`

`probe_id`, `kind` (outcome), `started_at`, `ended_at` (null while open), `duration_s`,
`checks_count`.

## `v_probes`

The catalog, so the methodology page never hand-writes it: `id`, `name`, `group_name`, `host`,
`method`, `url_display`, `interval_s`, `timeout_s`, `degraded_ms`, `retired_at`, `sort`.

## `v_heartbeat`

One row per region. `region`, `last_seen`, `probe_version`, `silent_seconds`
(`floor(epoch(now() - last_seen))`) and `is_stale` (silent for more than 600 seconds).

The page says "sin datos" from this view, and the scheduled workflow opens an issue from it.
