-- A week of measurements for development, the e2e run and the screens.
-- Deterministic: the same seed produces the same page every time.

insert into public.probes (id, name, group_name, host, method, url_display, interval_s, timeout_s,
                           degraded_ms, enabled, sort)
values
  ('nsv-config', 'Configuración web', 'venta nueva', 'venta.rsv.renfe.com', 'GET',
   '/config/arch-config.json', 300, 10, 3000, true, 10),
  ('nsv-token', 'Token público', 'venta nueva', 'api.rsv.renfe.com', 'GET',
   '/user/external-users-login/v1/tokens/public', 300, 10, 3000, true, 20),
  ('nsv-stations', 'Catálogo de estaciones', 'venta nueva', 'api.rsv.renfe.com', 'GET',
   '/catalog/masterdata/v1/stations', 900, 10, 3000, true, 30),
  ('nsv-search', 'Búsqueda de viajes', 'venta nueva', 'api.rsv.renfe.com', 'POST',
   '/browsing/traveloptions/v1/search-travel', 900, 15, 5000, true, 40),
  ('legacy-shop', 'Buscador de trenes', 'venta clásica', 'venta.renfe.com', 'GET',
   'buscarTren.do + DWR generateId', 900, 15, 6000, true, 50),
  ('live-map', 'Mapa en vivo de larga distancia', 'información',
   'tiempo-real.largorecorrido.renfe.com', 'GET', '/renfe-visor/flotaLD.json', 60, 10, 2000,
   true, 60),
  ('gtfs-avld', 'Horarios GTFS AV/LD', 'información', 'ssl.renfe.com', 'GET',
   '/gtransit/Fichero_AV_LD/google_transit.zip', 900, 20, 5000, true, 70),
  ('www-search', 'Buscador de billetes', 'web', 'www.renfe.com', 'GET',
   '/es/es/buscador-de-billetes', 300, 10, 3000, true, 80)
on conflict (id) do nothing;

with series as (
  select
    p.id as probe_id,
    p.degraded_ms,
    generated as ts
  from public.probes p
  cross join lateral generate_series(
    now() - interval '7 days',
    now(),
    make_interval(secs => p.interval_s)
  ) as generated
),
decided as (
  select
    probe_id,
    degraded_ms,
    ts,
    case
      when probe_id = 'live-map'
        and ts >= now() - interval '4 days 2 hours'
        and ts < now() - interval '4 days'
        then 'down'::public.outcome_enum
      when probe_id = 'legacy-shop'
        and ts >= now() - interval '3 days 30 minutes'
        and ts < now() - interval '3 days'
        then 'degraded'::public.outcome_enum
      when probe_id = 'legacy-shop'
        and ts >= now() - interval '2 days 1 hour'
        and ts < now() - interval '2 days'
        then 'blocked'::public.outcome_enum
      when probe_id = 'nsv-search'
        and ts >= now() - interval '1 day 45 minutes'
        and ts < now() - interval '1 day'
        then 'degraded'::public.outcome_enum
      when probe_id = 'www-search'
        and mod(extract(epoch from ts)::bigint / 300, 97) = 0
        then 'down'::public.outcome_enum
      else 'up'::public.outcome_enum
    end as outcome
  from series
)
insert into public.checks (probe_id, started_at, duration_ms, http_status, outcome, reason, region,
                           probe_version)
select
  decided.probe_id,
  decided.ts,
  case decided.outcome
    when 'up' then 40 + (extract(epoch from decided.ts)::bigint % 260)
    when 'degraded' then decided.degraded_ms + 1500
    when 'blocked' then 35
    else 12000
  end::integer as duration_ms,
  case decided.outcome
    when 'up' then 200
    when 'degraded' then 200
    when 'blocked' then 403
    else 503
  end as http_status,
  decided.outcome,
  case decided.outcome
    when 'up' then 'ok'
    when 'degraded' then 'slow'
    when 'blocked' then 'http_403'
    else 'http_5xx'
  end as reason,
  'es-madrid' as region,
  '0.1.0' as probe_version
from decided;

-- The incidents those outages would have opened, closed as the brief describes.
insert into public.incidents (probe_id, kind, started_at, ended_at, checks_count)
values
  ('live-map', 'down', now() - interval '4 days 2 hours', now() - interval '4 days', 120),
  ('legacy-shop', 'degraded', now() - interval '3 days 30 minutes', now() - interval '3 days', 2),
  ('legacy-shop', 'blocked', now() - interval '2 days 1 hour', now() - interval '2 days', 4)
on conflict do nothing;

insert into public.heartbeat (region, last_seen, probe_version)
values ('es-madrid', now(), '0.1.0')
on conflict (region) do update
  set last_seen = excluded.last_seen,
      probe_version = excluded.probe_version;
