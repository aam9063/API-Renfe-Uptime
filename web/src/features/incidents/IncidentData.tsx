import type { IncidentRow, StatusNowRow } from '../../data/hooks'

import { incidentBadge } from '../../ui/outcome'
import { formatDuration, formatRelative } from '../../lib/format'

// The recent incidents, mapped from `v_incidents`. The view tells us the kind,
// the window and how many checks were involved; the cause itself is ours to
// explain in the same words the methodology uses.

export type IncidentItem = {
  probeId: string
  kind: string
  badge: string
  title: string
  text: string
  when: string
}

function titleFor(kind: string, name: string): string {
  if (kind === 'down') {
    return `${name} no respondió`
  }
  if (kind === 'degraded') {
    return `${name} respondió lento`
  }
  if (kind === 'blocked') {
    return `${name} devolvió un bloqueo a la sonda`
  }
  return `${name} sin datos suficientes`
}

function textFor(kind: string, checksCount: number): string {
  if (kind === 'down') {
    return `Contado como caída: ${checksCount} fallos seguidos y el endpoint de control respondía.`
  }
  if (kind === 'degraded') {
    return `Superó el umbral de degradado en ${checksCount} sondas seguidas; el servicio seguía respondiendo.`
  }
  if (kind === 'blocked') {
    return 'Renfe respondió con un bloqueo. No cuenta como caída ni suma al uptime: no sabemos cómo lo veía un usuario normal.'
  }
  return 'No sabemos lo que vio un usuario normal en este tramo, así que no cuenta para el uptime.'
}

export function buildIncidents(
  incidentRows: readonly IncidentRow[],
  statusRows: readonly StatusNowRow[],
  nowIso: string,
): IncidentItem[] {
  const nameByProbe = new Map(statusRows.map((row) => [row.probe_id, row.name]))
  return incidentRows.map((row) => {
    const badge = incidentBadge(row.kind)
    const name = nameByProbe.get(row.probe_id) ?? row.probe_id
    const when =
      row.ended_at === null
        ? `en curso, ${formatRelative(row.started_at, nowIso)} empezó`
        : `${formatRelative(row.ended_at, nowIso)} · ${formatDuration(row.duration_s)}`
    return {
      probeId: row.probe_id,
      kind: row.kind,
      badge: badge.className,
      title: titleFor(row.kind, name),
      text: textFor(row.kind, row.checks_count),
      when,
    }
  })
}

export function IncidentCard({ incident }: { incident: IncidentItem }) {
  return (
    <article className="flex flex-wrap items-baseline gap-x-6 gap-y-2 rounded-xl border border-line bg-surface px-5 py-4 md:px-6">
      <span
        className={`self-start rounded-full px-2.5 py-1 text-[12px] font-semibold ${incident.badge}`}
      >
        {incidentBadge(incident.kind).label}
      </span>
      <div className="min-w-0 flex-[1_1_360px]">
        <h3 className="m-0 text-[15px] font-semibold">{incident.title}</h3>
        <p className="m-0 mt-1 text-[14px] leading-relaxed text-ink-soft">{incident.text}</p>
      </div>
      <span className="font-mono text-[13px] text-muted">{incident.when}</span>
    </article>
  )
}
