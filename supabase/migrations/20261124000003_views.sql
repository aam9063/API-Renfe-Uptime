-- The public views. They are the only thing the web reads, and they glue the formula to real rows.

create or replace view public.v_probes with (security_invoker = false) as
select
  id, name, group_name, host, method, url_display,
  interval_s, timeout_s, degraded_ms, retired_at, sort
from public.probes
where enabled;

create or replace view public.v_status_now with (security_invoker = false) as
select
  p.id as probe_id,
  p.name,
  p.group_name,
  p.host,
  case
    when last.started_at is null
      or last.started_at < now() - make_interval(secs => p.interval_s * 2)
      then 'unknown'::public.outcome_enum
    else last.outcome
  end as outcome,
  case
    when last.started_at is null
      or last.started_at < now() - make_interval(secs => p.interval_s * 2)
      then 'gap'
    else last.reason
  end as reason,
  last.started_at as last_check_at,
  last.duration_ms
from public.probes p
left join lateral (
  select c.outcome, c.reason, c.started_at, c.duration_ms
  from public.checks c
  where c.probe_id = p.id
  order by c.started_at desc
  limit 1
) last on true
where p.enabled;

create or replace view public.v_uptime_windows with (security_invoker = false) as
with windows (window_key, window_label, window_seconds) as (
  values
    ('24h', 'últimas 24 horas', 86400),
    ('7d', 'últimos 7 días', 604800),
    ('30d', 'últimos 30 días', 2592000),
    ('90d', 'últimos 90 días', 7776000)
),
totals as (
  select
    p.id as probe_id,
    w.window_key,
    w.window_label,
    w.window_seconds,
    coalesce(sum(s.seconds) filter (where s.outcome = 'up'), 0)::bigint as up_seconds,
    coalesce(sum(s.seconds) filter (where s.outcome = 'degraded'), 0)::bigint as degraded_seconds,
    coalesce(sum(s.seconds) filter (where s.outcome = 'down'), 0)::bigint as down_seconds,
    coalesce(sum(s.seconds) filter (where s.outcome = 'blocked'), 0)::bigint as blocked_seconds
  from public.probes p
  cross join windows w
  left join lateral public.probe_seconds(
    p.id,
    now() - make_interval(secs => w.window_seconds),
    now()
  ) s on true
  where p.enabled
  group by p.id, w.window_key, w.window_label, w.window_seconds
)
select
  totals.probe_id,
  totals.window_key,
  totals.window_label,
  summary.available_seconds,
  summary.denominator_seconds,
  summary.down_seconds,
  summary.uptime,
  summary.display_percent,
  summary.nines,
  summary.insufficient,
  summary.no_downtime
from totals
cross join lateral public.uptime_summary(
  totals.up_seconds,
  totals.degraded_seconds,
  totals.down_seconds,
  totals.blocked_seconds,
  0,
  totals.window_seconds
) summary;

create or replace view public.v_daily_90 with (security_invoker = false) as
with per_day as (
  select
    p.id as probe_id,
    d.day,
    coalesce(sum(d.seconds) filter (where d.outcome = 'up'), 0)::bigint as up_seconds,
    coalesce(sum(d.seconds) filter (where d.outcome = 'degraded'), 0)::bigint as degraded_seconds,
    coalesce(sum(d.seconds) filter (where d.outcome = 'down'), 0)::bigint as down_seconds,
    coalesce(sum(d.seconds) filter (where d.outcome = 'blocked'), 0)::bigint as blocked_seconds
  from public.probes p
  cross join lateral public.daily_seconds(p.id, 90) d
  where p.enabled
  group by p.id, d.day
)
select
  per_day.probe_id,
  per_day.day,
  case
    when per_day.down_seconds > 0 then 'down'::public.outcome_enum
    when per_day.degraded_seconds > 0 then 'degraded'::public.outcome_enum
    when per_day.blocked_seconds > 0 then 'blocked'::public.outcome_enum
    when per_day.up_seconds > 0 then 'up'::public.outcome_enum
    else 'unknown'::public.outcome_enum
  end as worst_outcome,
  summary.uptime,
  summary.display_percent
from per_day
cross join lateral public.uptime_summary(
  per_day.up_seconds,
  per_day.degraded_seconds,
  per_day.down_seconds,
  per_day.blocked_seconds,
  0,
  86400
) summary;

create or replace view public.v_latency_24h with (security_invoker = false) as
select
  c.probe_id,
  to_timestamp(floor(extract(epoch from c.started_at) / 1800) * 1800) as bucket_start,
  percentile_cont(0.5) within group (order by c.duration_ms)::integer as p50_ms,
  percentile_cont(0.95) within group (order by c.duration_ms)::integer as p95_ms
from public.checks c
where c.started_at > now() - interval '24 hours'
  and c.outcome in ('up', 'degraded')
group by c.probe_id, 2;

create or replace view public.v_recent_checks with (security_invoker = false) as
select probe_id, started_at, outcome, http_status, duration_ms
from (
  select
    c.probe_id,
    c.started_at,
    c.outcome,
    c.http_status,
    c.duration_ms,
    row_number() over (partition by c.probe_id order by c.started_at desc) as position
  from public.checks c
) ranked
where ranked.position <= 50;

create or replace view public.v_incidents with (security_invoker = false) as
select
  i.probe_id,
  i.kind,
  i.started_at,
  i.ended_at,
  case
    when i.ended_at is null then null
    else floor(extract(epoch from (i.ended_at - i.started_at)))::bigint
  end as duration_s,
  i.checks_count
from public.incidents i
order by i.started_at desc;

create or replace view public.v_heartbeat with (security_invoker = false) as
select
  h.region,
  h.last_seen,
  h.probe_version,
  floor(extract(epoch from (now() - h.last_seen)))::bigint as silent_seconds,
  now() - h.last_seen > interval '10 minutes' as is_stale
from public.heartbeat h;
