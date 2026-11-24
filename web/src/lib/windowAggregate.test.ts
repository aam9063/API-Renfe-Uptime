import { describe, expect, it } from 'vitest'

import type { UptimeWindowRow } from '../data/hooks'

import { displayPercent } from './format'
import { aggregateWindows } from './windowAggregate'

function windowRow(overrides: Partial<UptimeWindowRow>): UptimeWindowRow {
  return {
    probe_id: 'probe',
    window_key: '30d',
    window_label: '30 días',
    uptime: null,
    display_percent: null,
    nines: null,
    down_seconds: 0,
    denominator_seconds: 100000,
    insufficient: false,
    no_downtime: false,
    ...overrides,
  }
}

describe('aggregateWindows', () => {
  it('computes the unweighted mean of the exact fractions', () => {
    const aggregate = aggregateWindows(
      [
        windowRow({ probe_id: 'a', down_seconds: 100 }),
        windowRow({ probe_id: 'b', down_seconds: 0 }),
      ],
      '30d',
    )
    expect(aggregate.serviceCount).toBe(2)
    expect(aggregate.uptime).toBe('1999/2000')
    expect(displayPercent(aggregate.uptime)).toBe('99,95')
    expect(aggregate.downSeconds).toBe(100)
  })

  it('only counts the requested window', () => {
    const aggregate = aggregateWindows(
      [windowRow({ window_key: '7d', down_seconds: 100 })],
      '30d',
    )
    expect(aggregate.serviceCount).toBe(0)
    expect(aggregate.uptime).toBeNull()
    expect(aggregate.nines).toBeNull()
  })

  it('excludes the services without data, never counts them as down', () => {
    const aggregate = aggregateWindows(
      [
        windowRow({ probe_id: 'a', down_seconds: 4 }),
        windowRow({ probe_id: 'sin-datos', denominator_seconds: 0, down_seconds: 5000 }),
      ],
      '30d',
    )
    expect(aggregate.serviceCount).toBe(1)
    expect(aggregate.uptime).toBe('24999/25000')
    expect(displayPercent(aggregate.uptime)).toBe('99,99')
    expect(aggregate.nines).toBe(4)
    expect(aggregate.downSeconds).toBe(4)
  })

  it('gives no nines when nothing fell in any service', () => {
    const aggregate = aggregateWindows(
      [windowRow({ probe_id: 'a' }), windowRow({ probe_id: 'b', down_seconds: 0 })],
      '30d',
    )
    expect(aggregate.nines).toBeNull()
  })

  it('keeps exactness even when the common denominator is astronomical', () => {
    const aggregate = aggregateWindows(
      [
        windowRow({ probe_id: 'a', denominator_seconds: 2592000, down_seconds: 7775 }),
        windowRow({ probe_id: 'b', denominator_seconds: 7776000, down_seconds: 23208 }),
      ],
      '30d',
    )
    // Both fractions are 0.997: the reduced mean must display 99,70 (truncated).
    expect(aggregate.uptime).toBe('5168489/5184000')
    expect(displayPercent(aggregate.uptime)).toBe('99,70')
    expect(aggregate.nines).toBe(2)
    expect(aggregate.downSeconds).toBe(30983)
  })
})
