// The five outcomes of the domain and how the design paints them. `blocked`
// is a hatch: shown, but never counted as downtime. Anything unknown or
// missing reads as "sin datos".

export type OutcomeStyle = {
  className: string
  label: string
}

export function dailyBarClass(outcome: string): string {
  switch (outcome) {
    case 'up':
      return 'bg-up'
    case 'degraded':
      return 'bg-degraded'
    case 'down':
      return 'bg-down'
    case 'blocked':
      return 'bg-blocked-stripes'
    default:
      return 'bg-nodata'
  }
}

export function latencyBarClass(hasNoResponse: boolean, overThreshold: boolean): string {
  if (hasNoResponse) {
    return 'opacity-35 bg-down'
  }
  return overThreshold ? 'bg-degraded' : 'bg-link'
}

export function statusPill(outcome: string): OutcomeStyle {
  switch (outcome) {
    case 'up':
      return { className: 'bg-up-surface text-up-ink', label: 'Operativo' }
    case 'degraded':
      return { className: 'bg-degraded-surface text-degraded-ink', label: 'Degradado' }
    case 'down':
      return { className: 'bg-down-surface text-down-ink', label: 'Caído' }
    case 'blocked':
      return { className: 'bg-blocked-surface text-blocked-ink', label: 'Bloqueado' }
    case 'unknown':
      return { className: 'bg-neutral-surface text-ink-soft', label: 'Sin datos' }
    default:
      return { className: 'bg-neutral-surface text-ink-soft', label: 'Sin datos' }
  }
}

export function checkBadge(outcome: string): OutcomeStyle {
  switch (outcome) {
    case 'up':
      return { className: 'bg-up-surface text-up-ink', label: 'Operativo' }
    case 'degraded':
      return { className: 'bg-degraded-surface text-degraded-ink', label: 'Degradado' }
    case 'down':
      return { className: 'bg-down-surface text-down-ink', label: 'Caído' }
    default:
      return { className: 'bg-neutral-surface text-ink-soft', label: 'Sin datos' }
  }
}

export function incidentBadge(kind: string): OutcomeStyle {
  switch (kind) {
    case 'down':
      return { className: 'bg-down-surface text-down-ink', label: 'Caído' }
    case 'degraded':
      return { className: 'bg-degraded-surface text-degraded-ink', label: 'Degradado' }
    case 'blocked':
      return { className: 'bg-blocked-surface text-blocked-ink', label: 'Bloqueado' }
    default:
      return { className: 'bg-neutral-surface text-ink-soft', label: 'Sin datos' }
  }
}

export function legendChip(outcome: string): OutcomeStyle {
  switch (outcome) {
    case 'up':
      return { className: 'bg-up', label: 'Operativo' }
    case 'degraded':
      return { className: 'bg-degraded', label: 'Degradado' }
    case 'down':
      return { className: 'bg-down', label: 'Caído' }
    case 'blocked':
      return { className: 'bg-blocked-stripes', label: 'Bloqueado (no cuenta)' }
    default:
      return { className: 'bg-nodata', label: 'Sin datos' }
  }
}

export function statusDotClass(outcome: string): string {
  switch (outcome) {
    case 'up':
      return 'bg-up'
    case 'degraded':
      return 'bg-degraded'
    case 'down':
      return 'bg-down'
    default:
      return 'bg-nodata'
  }
}
