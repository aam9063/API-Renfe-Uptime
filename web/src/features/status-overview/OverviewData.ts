import type { Daily90Row, Latency24hRow, ProbeRow, StatusNowRow, UptimeWindowRow } from '../../data/hooks'

import { formatDateWithYear, formatLatency } from '../../lib/format'
import { DESKTOP_STRIP_DAYS, MOBILE_STRIP_DAYS } from '../../lib/windows'

// The pure shaping of the home data: from view rows to renderable items, with
// no network and no React in between, so it can be tested directly.

export type ServiceListItem = {
  probeId: string
  name: string
  group: string
  checkLine: string
  host: string
  outcome: string
  lastCheckAt: string | null
  displayPercent: string | null
  insufficient: boolean
  noDowntime: boolean
  nines: number | null
  p95: string | null
  daily: Daily90Row[]
}

export type ServiceGroupItem = {
  name: string
  host: string
  retirementNote: string | null
  services: ServiceListItem[]
}

export type OverviewData = {
  groups: ServiceGroupItem[]
}

export type OverviewInput = {
  statusRows: readonly StatusNowRow[]
  windowRows: readonly UptimeWindowRow[]
  dailyRows: readonly Daily90Row[]
  latencyRows: readonly Latency24hRow[]
  probeRows: readonly ProbeRow[]
  windowKey: string
}

export function buildOverview(input: OverviewInput): OverviewData {
  const windowByProbe = new Map<string, UptimeWindowRow>()
  for (const row of input.windowRows) {
    if (row.window_key === input.windowKey) {
      windowByProbe.set(row.probe_id, row)
    }
  }
  const dailyByProbe = new Map<string, Daily90Row[]>()
  for (const row of input.dailyRows) {
    const days = dailyByProbe.get(row.probe_id) ?? []
    days.push(row)
    dailyByProbe.set(row.probe_id, days)
  }
  const latestLatency = new Map<string, Latency24hRow>()
  for (const row of input.latencyRows) {
    latestLatency.set(row.probe_id, row)
  }
  const probeById = new Map<string, ProbeRow>()
  for (const row of input.probeRows) {
    probeById.set(row.id, row)
  }

  const services: ServiceListItem[] = []
  for (const status of input.statusRows) {
    const window = windowByProbe.get(status.probe_id)
    const probe = probeById.get(status.probe_id)
    const latency = latestLatency.get(status.probe_id)
    services.push({
      probeId: status.probe_id,
      name: status.name,
      group: status.group_name,
      checkLine: probe === undefined ? status.host : `${probe.method} ${probe.url_display}`,
      host: status.host,
      outcome: status.outcome,
      lastCheckAt: status.last_check_at,
      displayPercent: window?.display_percent ?? null,
      insufficient: window?.insufficient ?? true,
      noDowntime: window?.no_downtime ?? false,
      nines: window?.nines ?? null,
      p95: formatLatency(latency?.p95_ms ?? null),
      daily: dailyByProbe.get(status.probe_id) ?? [],
    })
  }

  const hostsByGroup = new Map<string, Set<string>>()
  const retirementByGroup = new Map<string, string>()
  for (const service of services) {
    const hosts = hostsByGroup.get(service.group) ?? new Set<string>()
    hosts.add(service.host)
    hostsByGroup.set(service.group, hosts)
    const retired = probeById.get(service.probeId)?.retired_at ?? null
    if (retired !== null && !retirementByGroup.has(service.group)) {
      retirementByGroup.set(
        service.group,
        `Se retira con la venta nueva (${formatDateWithYear(retired)})`,
      )
    }
  }

  const groups: ServiceGroupItem[] = []
  for (const service of services) {
    let group = groups.find((candidate) => candidate.name === service.group)
    if (group === undefined) {
      group = {
        name: service.group,
        host: [...(hostsByGroup.get(service.group) ?? [])].join(' · '),
        retirementNote: retirementByGroup.get(service.group) ?? null,
        services: [],
      }
      groups.push(group)
    }
    group.services.push(service)
  }
  return { groups }
}

export const STRIP_DAYS = { desktop: DESKTOP_STRIP_DAYS, mobile: MOBILE_STRIP_DAYS } as const
