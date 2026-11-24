-- `anon` reads the public views and nothing else. No table is writable, no table is readable.

revoke all on table public.probes from anon, authenticated;
revoke all on table public.checks from anon, authenticated;
revoke all on table public.incidents from anon, authenticated;
revoke all on table public.heartbeat from anon, authenticated;
revoke all on table public.daily_rollups from anon, authenticated;

grant select on table public.v_probes to anon, authenticated;
grant select on table public.v_status_now to anon, authenticated;
grant select on table public.v_uptime_windows to anon, authenticated;
grant select on table public.v_daily_90 to anon, authenticated;
grant select on table public.v_latency_24h to anon, authenticated;
grant select on table public.v_recent_checks to anon, authenticated;
grant select on table public.v_incidents to anon, authenticated;
grant select on table public.v_heartbeat to anon, authenticated;

-- The prober writes with the service role, which bypasses RLS by design in Supabase.
grant all on table public.probes to service_role;
grant all on table public.checks to service_role;
grant all on table public.incidents to service_role;
grant all on table public.heartbeat to service_role;
grant all on table public.daily_rollups to service_role;
grant usage, select on all sequences in schema public to service_role;
grant execute on function public.uptime_summary(bigint, bigint, bigint, bigint, bigint, bigint)
  to anon, authenticated, service_role;

-- Belt and braces: with RLS on and no policy, even a stray grant reads nothing.
drop policy if exists probes_read on public.probes;
create policy probes_read on public.probes for select to authenticated using (false);
