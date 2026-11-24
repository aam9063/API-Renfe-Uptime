import { describe, expect, it } from 'vitest'

import { buildLatencyBars } from './latencyBars'

describe('buildLatencyBars', () => {
  it('heights scale against the degraded threshold', () => {
    const bars = buildLatencyBars([500, 1000, 2000], 2000)
    expect(bars[0]).toEqual({ heightPercent: 25, className: 'bg-link' })
    expect(bars[1]).toEqual({ heightPercent: 50, className: 'bg-link' })
    expect(bars[2]).toEqual({ heightPercent: 100, className: 'bg-degraded' })
  })

  it('marks values over the threshold as degraded', () => {
    const bars = buildLatencyBars([1990, 2310], 2000)
    expect(bars[0]?.className).toBe('bg-link')
    expect(bars[1]?.className).toBe('bg-degraded')
  })

  it('shows a full-height red bar where there was no answer', () => {
    for (const value of [null, 0]) {
      const bars = buildLatencyBars([value], 2000)
      expect(bars[0]).toEqual({ heightPercent: 100, className: 'opacity-35 bg-down' })
    }
  })

  it('never renders a bar shorter than a sliver', () => {
    const bars = buildLatencyBars([7], 2000)
    expect(bars[0]?.heightPercent).toBe(4)
  })

  it('clamps huge values to the full height', () => {
    const bars = buildLatencyBars([999999], 2000)
    expect(bars[0]?.heightPercent).toBe(100)
    expect(bars[0]?.className).toBe('bg-degraded')
  })

  it('uses the full height when the threshold is unknown', () => {
    const bars = buildLatencyBars([318], 0)
    expect(bars[0]).toEqual({ heightPercent: 100, className: 'bg-link' })
  })
})
