-- Retention: raw checks live 120 days, the daily rollups live forever.

create or replace function public.rollup_closed_days(p_days integer default 2)
returns integer
language plpgsql
as $$
declare
  affected integer;
begin
  insert into public.daily_rollups as r (
    probe_id, day, up_seconds, degraded_seconds, down_seconds, blocked_seconds, unknown_seconds
  )
  select
    d.probe_id,
    d.day,
    coalesce(sum(d.seconds) filter (where d.outcome = 'up'), 0),
    coalesce(sum(d.seconds) filter (where d.outcome = 'degraded'), 0),
    coalesce(sum(d.seconds) filter (where d.outcome = 'down'), 0),
    coalesce(sum(d.seconds) filter (where d.outcome = 'blocked'), 0),
    0
  from (
    select
      p.id as probe_id,
      s.day,
      s.outcome,
      s.seconds
    from public.probes p
    cross join lateral public.daily_seconds(p.id, p_days) s
    where s.day < (now() at time zone 'Europe/Madrid')::date
  ) d
  group by d.probe_id, d.day
  on conflict (probe_id, day) do update set
    up_seconds = excluded.up_seconds,
    degraded_seconds = excluded.degraded_seconds,
    down_seconds = excluded.down_seconds,
    blocked_seconds = excluded.blocked_seconds,
    unknown_seconds = excluded.unknown_seconds;

  get diagnostics affected = row_count;
  return affected;
end;
$$;

create or replace function public.prune_checks(p_keep_days integer default 120)
returns bigint
language plpgsql
as $$
declare
  removed bigint;
begin
  -- The rollups are written first, so a prune never loses a day it still needs.
  perform public.rollup_closed_days(2);

  delete from public.checks where started_at < now() - make_interval(days => p_keep_days);
  get diagnostics removed = row_count;
  return removed;
end;
$$;

comment on function public.prune_checks(integer) is
  'Call daily from the Supabase cron job: rollups first, then delete checks older than p_keep_days.';
