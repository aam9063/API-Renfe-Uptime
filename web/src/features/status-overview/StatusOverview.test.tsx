import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { Daily90Row, ProbeRow, StatusNowRow, UptimeWindowRow } from '../../data/hooks'

import { AggregateCard } from './AggregateCard'
import { buildOverview } from './OverviewData'
import { DailyStrip } from '../../ui/DailyStrip'
import { ServiceGroups } from './ServiceGroups'
import { StatusOverview } from '.'

function windowRow(overrides: Partial<UptimeWindowRow>): UptimeWindowRow {
  return {
    probe_id: 'live-map',
    window_key: '30d',
    window_label: '30 días',
    uptime: '0.99996',
    display_percent: '99,99',
    nines: 4,
    down_seconds: 4,
    denominator_seconds: 100000,
    insufficient: false,
    no_downtime: false,
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

function dailyRow(overrides: Partial<Daily90Row>): Daily90Row {
  return {
    probe_id: 'live-map',
    day: '2026-01-01',
    worst_outcome: 'up',
    uptime: '1',
    display_percent: '100,00',
    ...overrides,
  }
}

function probeRow(overrides: Partial<ProbeRow> = {}): ProbeRow {
  return {
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
    ...overrides,
  }
}

describe('buildOverview', () => {
  it('groups the services and joins the unique hosts', () => {
    const overview = buildOverview({
      statusRows: [
        statusRow({ probe_id: 'config', group_name: 'Venta nueva' }),
        statusRow({ probe_id: 'live-map', group_name: 'Tiempo real' }),
        statusRow({ probe_id: 'stations', group_name: 'Venta nueva', host: 'api.rsv.renfe.com' }),
      ],
      windowRows: [],
      dailyRows: [],
      latencyRows: [],
      probeRows: [],
      windowKey: '30d',
    })
    expect(overview.groups.length).toBe(2)
    expect(overview.groups[0]?.name).toBe('Venta nueva')
    expect(overview.groups[0]?.host).toBe('tiempo-real.largorecorrido.renfe.com · api.rsv.renfe.com')
    expect(overview.groups[1]?.name).toBe('Tiempo real')
    expect(overview.groups[1]?.host).toBe('tiempo-real.largorecorrido.renfe.com')
  })

  it('brings the window, the latency and the catalog data of each service', () => {
    const overview = buildOverview({
      statusRows: [statusRow({ probe_id: 'live-map' })],
      windowRows: [windowRow({ window_key: '7d' })],
      dailyRows: [dailyRow({ day: '2026-01-01', worst_outcome: 'down' })],
      latencyRows: [
        {
          probe_id: 'live-map',
          bucket_start: '2026-02-06T15:30:00Z',
          p50_ms: 318,
          p95_ms: 640,
        },
      ],
      probeRows: [probeRow({ retired_at: '2027-01-25T00:00:00Z' })],
      windowKey: '30d',
    })
    const service = overview.groups[0]?.services[0]
    expect(service?.displayPercent).toBeNull()
    expect(service?.p95).toBe('640 ms')
    expect(service?.daily.length).toBe(1)
    expect(service?.checkLine).toBe('GET tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json')
    expect(overview.groups[0]?.retirementNote).toBe('Se retira con la venta nueva (25 ene 2027)')
  })
})

describe('AggregateCard', () => {
  it('shows the aggregate percent of the selected window', () => {
    render(
      <AggregateCard
        windowRows={[
          windowRow({ probe_id: 'a', down_seconds: 4 }),
          windowRow({ probe_id: 'b', down_seconds: 0 }),
        ]}
        selected="30d"
        onSelect={() => undefined}
      />,
    )
    expect(screen.getByText('99,99')).toBeDefined()
    expect(screen.getByText('4 s caído en total')).toBeDefined()
  })

  it('changes window through the tabs', () => {
    const onSelect = vi.fn()
    render(
      <AggregateCard windowRows={[windowRow({ probe_id: 'a' })]} selected="30d" onSelect={onSelect} />,
    )
    fireEvent.click(screen.getByRole('tab', { name: '90d' }))
    expect(onSelect).toHaveBeenCalledWith('90d')
  })

  it('renders Sin datos when the window has no services with data', () => {
    render(
      <AggregateCard windowRows={[windowRow({ denominator_seconds: 0 })]} selected="30d" onSelect={() => undefined} />,
    )
    expect(screen.getByText('Sin datos')).toBeDefined()
  })
})

describe('DailyStrip', () => {
  it('pads missing days with sin datos bars', () => {
    const { container } = render(
      <div>
        <DailyStrip
          days={3}
          rows={[dailyRow({ worst_outcome: 'down' }), dailyRow({ day: '2026-01-02' })]}
          label="prueba"
        />
      </div>,
    )
    expect(container.querySelectorAll('.bg-nodata').length).toBe(1)
    expect(container.querySelectorAll('.bg-down').length).toBe(1)
    expect(container.querySelectorAll('.bg-up').length).toBe(1)
  })
})

describe('ServiceGroups', () => {
  it('renders a group with its services and the links to the detail', () => {
    const overview = buildOverview({
      statusRows: [statusRow({ probe_id: 'live-map' })],
      windowRows: [windowRow({ probe_id: 'live-map' })],
      dailyRows: [],
      latencyRows: [],
      probeRows: [probeRow()],
      windowKey: '30d',
    })
    render(<ServiceGroups groups={overview.groups} />)
    expect(screen.getByRole('heading', { name: 'Servicios' })).toBeDefined()
    const links = screen.getAllByText('Mapa en vivo').map((element) => element.closest('a'))
    expect(links.length).toBe(2)
    for (const link of links) {
      expect(link?.getAttribute('href')).toBe('/servicio/live-map')
    }
  })
})

describe('StatusOverview without configuration', () => {
  it('renders Sin datos instead of crashing', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <StatusOverview />
      </QueryClientProvider>,
    )
    expect(screen.getAllByText('Sin datos').length).toBeGreaterThan(0)
  })
})
