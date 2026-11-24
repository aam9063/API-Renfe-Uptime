import { useQuery, type UseQueryResult } from '@tanstack/react-query'

import { isConfigured, supabase } from './client'

// One hook per view, exactly the columns the M3 view contract defines. The
// web reads views (`v_*`), never tables.

export type StatusNowRow = {
  probe_id: string
  name: string
  group_name: string
  host: string
  outcome: string
  reason: string | null
  last_check_at: string | null
  duration_ms: number | null
}

export type UptimeWindowRow = {
  probe_id: string
  window_key: string
  window_label: string
  uptime: string | null
  display_percent: string | null
  nines: number | null
  down_seconds: number
  denominator_seconds: number
  insufficient: boolean
  no_downtime: boolean
}

export type Daily90Row = {
  probe_id: string
  day: string
  worst_outcome: string
  uptime: string | null
  display_percent: string | null
}

export type Latency24hRow = {
  probe_id: string
  bucket_start: string
  p50_ms: number | null
  p95_ms: number | null
}

export type RecentCheckRow = {
  probe_id: string
  started_at: string
  outcome: string
  http_status: number | null
  duration_ms: number | null
}

export type IncidentRow = {
  probe_id: string
  kind: string
  started_at: string
  ended_at: string | null
  duration_s: number
  checks_count: number
}

export type ProbeRow = {
  id: string
  name: string
  group_name: string
  host: string
  method: string
  url_display: string
  interval_s: number
  timeout_s: number
  degraded_ms: number
  retired_at: string | null
  sort: number
}

type FetchOptions = {
  order?: string
  ascending?: boolean
  limit?: number
}

const RECENT_CHECKS_LIMIT = 8

async function fetchRows<Row>(view: string, options: FetchOptions = {}): Promise<Row[]> {
  if (supabase === null) {
    return []
  }
  let request = supabase.from(view).select('*')
  if (options.order !== undefined) {
    request = request.order(options.order, { ascending: options.ascending ?? true })
  }
  if (options.limit !== undefined) {
    request = request.limit(options.limit)
  }
  const { data, error } = await request
  if (error !== null) {
    throw new Error(`La vista ${view} respondió: ${error.message}`)
  }
  return (data ?? []) as unknown as Row[]
}

function useView<Row>(view: string, key: readonly unknown[], options: FetchOptions = {}) {
  return useQuery({
    queryKey: [view, ...key],
    queryFn: () => fetchRows<Row>(view, options),
    enabled: isConfigured,
  })
}

export function useStatusNow(): UseQueryResult<StatusNowRow[], Error> {
  return useView<StatusNowRow>('v_status_now', [])
}

export function useUptimeWindows(): UseQueryResult<UptimeWindowRow[], Error> {
  return useView<UptimeWindowRow>('v_uptime_windows', [])
}

export function useDaily90(): UseQueryResult<Daily90Row[], Error> {
  return useView<Daily90Row>('v_daily_90', [], { order: 'day' })
}

export function useLatency24h(): UseQueryResult<Latency24hRow[], Error> {
  return useView<Latency24hRow>('v_latency_24h', [], { order: 'bucket_start' })
}

export function useRecentChecks(probeId: string): UseQueryResult<RecentCheckRow[], Error> {
  return useView<RecentCheckRow>('v_recent_checks', [probeId], {
    order: 'started_at',
    ascending: false,
    limit: RECENT_CHECKS_LIMIT,
  })
}

export function useIncidents(): UseQueryResult<IncidentRow[], Error> {
  return useView<IncidentRow>('v_incidents', [], { order: 'started_at', ascending: false })
}

export function useProbes(): UseQueryResult<ProbeRow[], Error> {
  return useView<ProbeRow>('v_probes', [], { order: 'sort' })
}
