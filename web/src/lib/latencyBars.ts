import { latencyBarClass } from '../ui/outcome'

// The bars of the latency chart. Heights scale against the degraded threshold
// of the probe (the same number the classifier uses); a bucket with no answer
// is a red full-height bar.

export type LatencyBar = {
  heightPercent: number
  className: string
}

/** The label of the middle grid line, rounded. */
export function midpointOf(value: number): number {
  return Math.round(value / 2)
}

const MIN_BAR_PERCENT = 4

export function buildLatencyBars(values: readonly (number | null)[], thresholdMs: number): LatencyBar[] {
  return values.map((value) => {
    if (value === null || value <= 0) {
      return { heightPercent: 100, className: latencyBarClass(true, false) }
    }
    if (thresholdMs <= 0) {
      return { heightPercent: 100, className: latencyBarClass(false, false) }
    }
    const raw = (value / thresholdMs) * 100
    const heightPercent = Math.min(100, Math.max(MIN_BAR_PERCENT, raw))
    return { heightPercent, className: latencyBarClass(false, value >= thresholdMs) }
  })
}
