import contract from '../../../contracts/uptime_cases.json'
import { describe, expect, it } from 'vitest'

import {
  displayPercent,
  formatClock,
  formatDay,
  formatDateWithYear,
  formatDuration,
  formatInterval,
  formatLatency,
  formatRelative,
  ninesText,
  windowLabel,
} from './format'

describe('the shared uptime contract', () => {
  it('reproduces the display_percent of every case', () => {
    for (const testCase of contract.cases) {
      const expected = testCase.expect
      const fraction =
        expected.denominator_seconds === 0
          ? null
          : `${expected.available_seconds}/${expected.denominator_seconds}`

      expect(displayPercent(fraction), testCase.name).toBe(expected.display_percent)
    }
  })

  it('reproduces the label of every case', () => {
    for (const testCase of contract.cases) {
      const expected = testCase.expect

      expect(
        windowLabel({ insufficient: expected.insufficient, noDowntime: expected.down_seconds === 0 }),
        testCase.name,
      ).toBe(expected.label)
    }
  })
})

describe('displayPercent', () => {
  it('truncates instead of rounding', () => {
    expect(displayPercent('99996/100000')).toBe('99,99')
    expect(displayPercent('99999/100000')).toBe('99,99')
  })

  it('accepts the numeric uptime of the views', () => {
    expect(displayPercent('1')).toBe('100,00')
    expect(displayPercent('0.99996')).toBe('99,99')
    expect(displayPercent('0.9912')).toBe('99,12')
  })

  it('has no percent without a denominator', () => {
    expect(displayPercent(null)).toBeNull()
    expect(displayPercent('5/0')).toBeNull()
    expect(displayPercent('')).toBeNull()
    expect(displayPercent('not a number')).toBeNull()
  })
})

describe('ninesText', () => {
  it('uses the singular and the plural', () => {
    expect(ninesText(1, { insufficient: false })).toBe('1 nueve')
    expect(ninesText(2, { insufficient: false })).toBe('2 nueves')
    expect(ninesText(5, { insufficient: false })).toBe('5 nueves')
  })

  it('prefers the window label when it applies', () => {
    expect(ninesText(3, { insufficient: true })).toBe('datos insuficientes')
    expect(ninesText(null, { insufficient: false })).toBe('sin caídas')
    expect(ninesText(null, { insufficient: true })).toBe('datos insuficientes')
  })
})

describe('formatDuration', () => {
  it('formats the durations of the design', () => {
    expect(formatDuration(26)).toBe('26 s')
    expect(formatDuration(263)).toBe('4 min 23 s')
    expect(formatDuration(2280)).toBe('38 min')
    expect(formatDuration(3720)).toBe('1 h 02 min')
    expect(formatDuration(8040)).toBe('2 h 14 min')
    expect(formatDuration(26100)).toBe('7 h 15 min')
    expect(formatDuration(87840)).toBe('24 h 24 min')
    expect(formatDuration(0)).toBe('0 s')
  })
})

describe('formatLatency', () => {
  it('formats milliseconds and seconds with the Spanish comma', () => {
    expect(formatLatency(318)).toBe('318 ms')
    expect(formatLatency(1400)).toBe('1,4 s')
    expect(formatLatency(2310)).toBe('2,31 s')
    expect(formatLatency(2000)).toBe('2 s')
    expect(formatLatency(null)).toBe('n/d')
  })
})

describe('formatRelative', () => {
  const now = '2026-02-06T16:40:00Z'

  it('measures from the reference instant', () => {
    expect(formatRelative('2026-02-06T16:39:37Z', now)).toBe('hace 23 s')
    expect(formatRelative('2026-02-06T16:02:00Z', now)).toBe('hace 38 min')
    expect(formatRelative('2026-02-06T04:40:00Z', now)).toBe('hace 12 h')
    expect(formatRelative('2026-02-02T16:40:00Z', now)).toBe('hace 4 días')
    expect(formatRelative('2026-01-25T16:40:00Z', now)).toBe('hace 12 días')
    expect(formatRelative(now, now)).toBe('ahora')
  })
})

describe('formatClock and formatDay', () => {
  it('formats instants in the browser locale', () => {
    expect(formatClock('2026-02-06T15:38:12Z')).toMatch(/^\d{2}:\d{2}:\d{2}$/)
    expect(formatDay('2026-08-26T00:00:00Z')).toMatch(/^\d{2} .*$/)
    expect(formatDateWithYear('2027-01-25T00:00:00Z')).toMatch(/^25 .* 2027$/)
  })
})

describe('formatInterval', () => {
  it('speaks the catalog intervals', () => {
    expect(formatInterval(60)).toBe('1 min')
    expect(formatInterval(300)).toBe('5 min')
    expect(formatInterval(900)).toBe('15 min')
  })
})
