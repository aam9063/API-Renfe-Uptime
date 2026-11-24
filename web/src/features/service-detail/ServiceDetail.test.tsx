import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Latency24hRow, RecentCheckRow, UptimeWindowRow } from '../../data/hooks'

import { buildLatencyBars } from '../../lib/latencyBars'
import { ChecksTable } from './ChecksTable'
import { LatencyPanel } from './LatencyPanel'
import { ProbeRules } from './ProbeRules'
import { ServiceDetail } from '.'
import { WindowCards } from './WindowCards'

function windowRow(overrides: Partial<UptimeWindowRow>): UptimeWindowRow {
  return {
    probe_id: 'live-map',
    window_key: '30d',
    window_label: '30 días',
    uptime: '0.9871',
    display_percent: '98,71',
    nines: 1,
    down_seconds: 33360,
    denominator_seconds: 2592000,
    insufficient: false,
    no_downtime: false,
    ...overrides,
  }
}

function latencyRow(overrides: Partial<Latency24hRow> = {}): Latency24hRow {
  return {
    probe_id: 'live-map',
    bucket_start: '2026-02-06T15:30:00Z',
    p50_ms: 318,
    p95_ms: 640,
    ...overrides,
  }
}

function checkRow(overrides: Partial<RecentCheckRow> = {}): RecentCheckRow {
  return {
    probe_id: 'live-map',
    started_at: '2026-02-06T16:38:12Z',
    outcome: 'up',
    http_status: 200,
    duration_ms: 284,
    ...overrides,
  }
}

describe('WindowCards', () => {
  it('shows the four windows of the design', () => {
    render(
      <WindowCards
        rows={[
          windowRow({ window_label: '24 h', down_seconds: 5400 }),
          windowRow({ window_label: '7 días' }),
          windowRow({ window_label: '30 días' }),
          windowRow({ window_label: '90 días' }),
        ]}
      />,
    )
    const body = document.body.textContent ?? ''
    expect(body).toContain('24 h')
    expect(body).toContain('98,71 %')
    expect(body).toContain('1 nueve')
    expect(body).toContain('1 h 30 min caído')
  })

  it('renders Sin datos for a window without percent', () => {
    render(<WindowCards rows={[windowRow({ display_percent: null })]} />)
    expect(screen.getByText('Sin datos')).toBeDefined()
  })
})

describe('LatencyPanel', () => {
  it('renders the buckets and switches between p50 and p95', () => {
    render(<LatencyPanel rows={[latencyRow(), latencyRow({ p50_ms: 2310 })]} degradedMs={2000} />)
    expect(screen.getByRole('heading', { name: 'Latencia, últimas 24 h' })).toBeDefined()
    expect(screen.getByRole('tab', { name: 'p50' }).getAttribute('aria-selected')).toBe('true')
    expect(screen.getByText('Umbral de degradado').textContent).toContain('2 s')

    fireEvent.click(screen.getByRole('tab', { name: 'p95' }))
    expect(screen.getByRole('tab', { name: 'p95' }).getAttribute('aria-selected')).toBe('true')
  })

  it('shows n/d when there are no buckets', () => {
    render(<LatencyPanel rows={[]} degradedMs={null} />)
    expect(screen.getAllByText('n/d').length).toBeGreaterThan(0)
  })
})

describe('buildLatencyBars', () => {
  it('scales against the probe threshold', () => {
    const bars = buildLatencyBars([500, null], 1000)
    expect(bars[0]?.heightPercent).toBe(50)
    expect(bars[1]?.className).toContain('bg-down')
  })
})

describe('ChecksTable', () => {
  it('lists the recent checks without inventing details', () => {
    render(
      <ChecksTable
        rows={[
          checkRow(),
          checkRow({ outcome: 'down', http_status: null, duration_ms: 10000 }),
        ]}
      />,
    )
    const table = screen.getByRole('table')
    expect(table.textContent).toContain('Operativo')
    expect(table.textContent).toContain('Caído')
    expect(table.textContent).toContain('n/d')
    expect(table.textContent).not.toContain('Detalle')
  })

  it('explains when there is nothing yet', () => {
    render(<ChecksTable rows={[]} />)
    expect(screen.getByText('Aún no hay comprobaciones registradas.')).toBeDefined()
  })
})

describe('ProbeRules', () => {
  it('takes the interval and timeout from the catalog', () => {
    render(
      <ProbeRules
        probe={{
          id: 'live-map',
          name: 'Mapa en vivo',
          group_name: 'Tiempo real',
          host: 'tiempo-real.largorecorrido.renfe.com',
          method: 'GET',
          url_display: 'tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json',
          interval_s: 60,
          timeout_s: 10,
          degraded_ms: 2000,
          retired_at: null,
          sort: 6,
        }}
      />,
    )
    expect(screen.getByText('Cada 1 min, timeout de 10 s.')).toBeDefined()
    expect(screen.getByText('Qué comprueba la sonda')).toBeDefined()
  })
})

describe('ServiceDetail without configuration', () => {
  it('renders Sin datos instead of crashing', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <ServiceDetail probeId="live-map" />
      </QueryClientProvider>,
    )
    expect(screen.getAllByText('Sin datos').length).toBeGreaterThan(0)
  })
})
