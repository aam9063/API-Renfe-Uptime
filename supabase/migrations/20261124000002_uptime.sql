-- The formula, in one place, callable from the views and from the contract test.
-- Mirrors prober/src/anden9/domain/uptime.py: integer seconds, exact nines, truncated display.

-- Every check owns the time until the next one, capped at twice its nominal interval.
create or replace function public.probe_seconds(
  p_probe_id text,
  p_from timestamptz,
  p_to timestamptz
)
returns table (outcome public.outcome_enum, seconds bigint)
language sql
stable
security definer
set search_path = public
as $$
  with ordered as (
    select
      c.started_at,
      c.outcome,
      least(
        coalesce(
          lead(c.started_at) over (partition by c.probe_id order by c.started_at),
          p_to
        ),
        c.started_at + (p.interval_s * 2) * interval '1 second',
        p_to
      ) as ended_at
    from public.checks c
    join public.probes p on p.id = c.probe_id
    where c.probe_id = p_probe_id
      and c.started_at < p_to
      and c.started_at + (p.interval_s * 2) * interval '1 second' > p_from
  )
  select
    ordered.outcome,
    coalesce(
      sum(
        floor(
          extract(epoch from (ordered.ended_at - greatest(ordered.started_at, p_from)))
        )
      )::bigint,
      0
    ) as seconds
  from ordered
  where ordered.ended_at > p_from
  group by ordered.outcome;
$$;

-- Uptime, nines, truncation and the insufficient window, from whole seconds per state.
create or replace function public.uptime_summary(
  p_up bigint,
  p_degraded bigint,
  p_down bigint,
  p_blocked bigint,
  p_unknown bigint,
  p_window_seconds bigint
)
returns table (
  available_seconds bigint,
  denominator_seconds bigint,
  down_seconds bigint,
  uptime numeric,
  display_percent text,
  nines integer,
  insufficient boolean,
  no_downtime boolean
)
language sql
immutable
as $$
  with measured as (
    select
      p_up + p_degraded as available,
      p_up + p_degraded + p_down as denominator,
      p_down as down_seconds,
      (p_up + p_degraded + p_down) * 2 < p_window_seconds as insufficient
  ),
  uptime as (
    select
      measured.*,
      case
        when measured.denominator > 0
          then measured.available::numeric / measured.denominator
        else null
      end as ratio
    from measured
  )
  select
    uptime.available,
    uptime.denominator,
    uptime.down_seconds,
    uptime.ratio,
    case
      when uptime.ratio is null then null
      else
        -- Truncated to two decimals, with the comma the page prints.
        (
          trunc(uptime.available::numeric * 10000 / uptime.denominator)::bigint / 100
        )::text
        || ','
        || lpad(
             (trunc(uptime.available::numeric * 10000 / uptime.denominator)::bigint % 100)::text,
             2,
             '0'
           )
    end as display_percent,
    case
      when uptime.down_seconds = 0 or uptime.denominator = 0 then null
      -- Exact integer arithmetic: the largest n with 10^n <= denominator / down.
      else greatest(
        0,
        length(((uptime.denominator / uptime.down_seconds)::bigint)::text) - 1
      )::integer
    end as nines,
    uptime.insufficient,
    uptime.denominator > 0 and uptime.down_seconds = 0 as no_downtime
  from uptime;
$$;

-- Seconds per state by Madrid day, the shape the 90 day strip needs.
create or replace function public.daily_seconds(
  p_probe_id text,
  p_days integer
)
returns table (day date, outcome public.outcome_enum, seconds bigint)
language sql
stable
security definer
set search_path = public
as $$
  with bounds as (
    select
      (date_trunc('day', now() at time zone 'Europe/Madrid') - make_interval(days => p_days - 1))
        at time zone 'Europe/Madrid' as first_day
  ),
  ordered as (
    select
      c.started_at,
      c.outcome,
      least(
        coalesce(
          lead(c.started_at) over (partition by c.probe_id order by c.started_at),
          now()
        ),
        c.started_at + (p.interval_s * 2) * interval '1 second',
        now()
      ) as ended_at
    from public.checks c
    join public.probes p on p.id = c.probe_id
    cross join bounds
    where c.probe_id = p_probe_id
      and c.started_at >= bounds.first_day
  )
  select
    (ordered.started_at at time zone 'Europe/Madrid')::date as day,
    ordered.outcome,
    sum(
      floor(extract(epoch from (ordered.ended_at - ordered.started_at)))
    )::bigint as seconds
  from ordered
  where ordered.ended_at > ordered.started_at
  group by 1, 2;
$$;
