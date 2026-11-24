import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ProbeRow } from '../../data/hooks'

import { Methodology, ProbeCatalog } from '.'

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

describe('ProbeCatalog', () => {
  it('reads the catalog from the views, never from hand written HTML', () => {
    render(<ProbeCatalog probes={[probeRow()]} />)
    const table = screen.getByRole('table')
    expect(table.textContent).toContain('Mapa en vivo')
    expect(table.textContent).toContain('GET tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json'.slice(0, 40))
    expect(table.textContent).toContain('1 min')
  })
})

describe('Methodology', () => {
  it('explains the five states and the formula', () => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <Methodology />
      </QueryClientProvider>,
    )
    expect(screen.getByRole('heading', { name: 'Cómo medimos', level: 1 })).toBeDefined()
    for (const state of ['Operativo', 'Degradado', 'Caído', 'Bloqueado', 'Sin datos']) {
      expect(screen.getByText(state), state).toBeDefined()
    }
    expect(screen.getByText('uptime =')).toBeDefined()
    expect(screen.getByText('nueves =')).toBeDefined()
    expect(screen.getByText('Cuenta en contra')).toBeDefined()
    expect(screen.getAllByText('No cuenta').length).toBe(2)
  })

  it('credits renfe-cli', () => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <Methodology />
      </QueryClientProvider>,
    )
    const link = screen.getByRole('link', { name: 'renfe-cli' })
    expect(link.getAttribute('href')).toBe('https://github.com/luisgonzaleznf/renfe-cli')
  })

  it('admits the catalog needs data', () => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <Methodology />
      </QueryClientProvider>,
    )
    expect(screen.getByText('Catálogo sin datos.')).toBeDefined()
  })
})
