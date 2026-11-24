import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

import type { StatusNowRow, UptimeWindowRow } from './hooks'

const STATUS_ROWS: StatusNowRow[] = [
  {
    probe_id: 'live-map',
    name: 'Mapa en vivo',
    group_name: 'Tiempo real',
    host: 'tiempo-real.largorecorrido.renfe.com',
    outcome: 'up',
    reason: null,
    last_check_at: '2026-02-06T16:38:12Z',
    duration_ms: 284,
  },
]

const WINDOW_ROWS: UptimeWindowRow[] = [
  {
    probe_id: 'live-map',
    window_key: '30d',
    window_label: '30 días',
    uptime: '0.99999',
    display_percent: '99,99',
    nines: 5,
    down_seconds: 26,
    denominator_seconds: 2592000,
    insufficient: false,
    no_downtime: false,
  },
]

beforeEach(() => {
  vi.resetModules()
})

describe('the view hooks without Supabase configured', () => {
  it('stay disabled instead of calling the network', async () => {
    vi.unstubAllEnvs()
    const { useStatusNow } = await import('./hooks')

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useStatusNow(), { wrapper })

    await waitFor(() => expect(result.current.fetchStatus).toBe('idle'))
    expect(result.current.data).toBeUndefined()
    expect(result.current.isError).toBe(false)
  })
})

describe('the view hooks with Supabase configured', () => {
  beforeAll(() => {
    vi.stubEnv('VITE_SUPABASE_URL', 'https://stub.supabase.local')
    vi.stubEnv('VITE_SUPABASE_ANON_KEY', 'anon-key-for-tests')
  })

  it('run the query through a stub fetch, never a real network', async () => {
    const fetchStub = vi.fn(async (_request: string | URL | Request) =>
      new Response(JSON.stringify(WINDOW_ROWS), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchStub)

    const { useUptimeWindows } = await import('./hooks')
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useUptimeWindows(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(WINDOW_ROWS)
    expect(fetchStub).toHaveBeenCalledTimes(1)
    const firstCall = fetchStub.mock.calls[0]
    expect(String(firstCall?.[0])).toContain('v_uptime_windows')
  })

  it('surface a query error as an error, not as data', async () => {
    const fetchStub = vi.fn(
      async (_request: string | URL | Request) =>
        new Response(JSON.stringify({ message: 'permission denied' }), {
          status: 403,
          headers: { 'content-type': 'application/json' },
        }),
    )
    vi.stubGlobal('fetch', fetchStub)

    const { useStatusNow } = await import('./hooks')
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useStatusNow(), { wrapper })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.data).toBeUndefined()
  })
})

describe('STATUS_ROWS', () => {
  it('describe the status of the stub service', () => {
    expect(STATUS_ROWS[0]?.name).toBe('Mapa en vivo')
  })
})
