import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { IncidentRow, StatusNowRow } from '../../data/hooks'

import { buildIncidents, IncidentCard } from './IncidentData'
import { IncidentsList } from '.'

const NOW = '2026-02-06T16:40:00Z'

function incidentRow(overrides: Partial<IncidentRow> = {}): IncidentRow {
  return {
    probe_id: 'live-map',
    kind: 'down',
    started_at: '2026-02-02T14:26:00Z',
    ended_at: '2026-02-02T16:40:00Z',
    duration_s: 8040,
    checks_count: 2,
    ...overrides,
  }
}

function statusRow(overrides: Partial<StatusNowRow>): StatusNowRow {
  return {
    probe_id: 'live-map',
    name: 'Mapa en vivo',
    group_name: 'Tiempo real',
    host: 'tiempo-real.largorecorrido.renfe.com',
    outcome: 'up',
    reason: null,
    last_check_at: '2026-02-06T16:38:12Z',
    duration_ms: 284,
    ...overrides,
  }
}

describe('buildIncidents', () => {
  it('explains a down incident with the words of the methodology', () => {
    const items = buildIncidents([incidentRow()], [statusRow({})], NOW)
    const item = items[0]
    expect(item?.title).toBe('Mapa en vivo no respondió')
    expect(item?.text).toContain('2 fallos seguidos y el endpoint de control respondía')
    expect(item?.when).toContain('hace 4 días · 2 h 14 min')
  })

  it('explains a blocked incident as something that never counts', () => {
    const items = buildIncidents(
      [incidentRow({ kind: 'blocked', duration_s: 3720 })],
      [],
      NOW,
    )
    expect(items[0]?.title).toContain('devolvió un bloqueo a la sonda')
    expect(items[0]?.when).toContain('1 h 02 min')
  })

  it('marks ongoing incidents', () => {
    const items = buildIncidents(
      [incidentRow({ ended_at: null, started_at: '2026-02-06T16:10:00Z' })],
      [],
      NOW,
    )
    expect(items[0]?.when).toContain('en curso')
  })
})

describe('IncidentCard', () => {
  it('renders kind, cause and duration', () => {
    const items = buildIncidents([incidentRow()], [statusRow({})], NOW)
    render(<IncidentCard incident={items[0]!} />)
    expect(screen.getByText('Caído')).toBeDefined()
    expect(screen.getByRole('heading', { name: 'Mapa en vivo no respondió' })).toBeDefined()
  })
})

describe('IncidentsList without configuration', () => {
  it('renders Sin datos instead of hitting the network', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <IncidentsList />
      </QueryClientProvider>,
    )
    expect(screen.getAllByText('Sin datos').length).toBeGreaterThan(0)
  })
})
