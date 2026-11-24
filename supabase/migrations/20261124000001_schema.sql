-- The measurement schema of the brief, additive only.
-- Nothing here drops or rewrites a measurement.

create type public.outcome_enum as enum ('up', 'degraded', 'down', 'blocked', 'unknown');

create table public.probes (
  id text primary key,
  name text not null,
  group_name text not null,
  host text not null,
  method text not null,
  url_display text not null,
  interval_s integer not null check (interval_s >= 60),
  timeout_s numeric not null check (timeout_s > 0),
  degraded_ms integer not null check (degraded_ms > 0),
  enabled boolean not null default true,
  retired_at timestamptz,
  sort integer not null default 0
);

create table public.checks (
  id bigint generated always as identity primary key,
  probe_id text not null references public.probes (id) on delete cascade,
  started_at timestamptz not null,
  duration_ms integer not null check (duration_ms >= 0),
  http_status integer,
  outcome public.outcome_enum not null,
  reason text not null,
  region text not null,
  probe_version text not null
);

create index checks_probe_started_at on public.checks (probe_id, started_at desc);
create index checks_started_at on public.checks (started_at desc);

create table public.incidents (
  id bigint generated always as identity primary key,
  probe_id text not null references public.probes (id) on delete cascade,
  kind public.outcome_enum not null,
  started_at timestamptz not null,
  ended_at timestamptz,
  checks_count integer not null default 0
);

create index incidents_probe_started_at on public.incidents (probe_id, started_at desc);
create unique index incidents_one_open_per_probe
  on public.incidents (probe_id)
  where ended_at is null;

create table public.heartbeat (
  region text primary key,
  last_seen timestamptz not null,
  probe_version text not null
);

-- Daily rollups survive the 120 day pruning of the raw checks.
create table public.daily_rollups (
  probe_id text not null references public.probes (id) on delete cascade,
  day date not null,
  up_seconds bigint not null default 0,
  degraded_seconds bigint not null default 0,
  down_seconds bigint not null default 0,
  blocked_seconds bigint not null default 0,
  unknown_seconds bigint not null default 0,
  primary key (probe_id, day)
);

alter table public.probes enable row level security;
alter table public.checks enable row level security;
alter table public.incidents enable row level security;
alter table public.heartbeat enable row level security;
alter table public.daily_rollups enable row level security;
