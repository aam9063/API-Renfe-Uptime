// The time windows the views publish, as a shared vocabulary for the features.
// The windows themselves and their labels come from `v_uptime_windows`;
// these constants only fix the order and the long copy of the design.

export const WINDOW_KEYS = ['24h', '7d', '30d', '90d'] as const

export type WindowKey = (typeof WINDOW_KEYS)[number]

export const WINDOW_LONG_LABELS: Readonly<Record<WindowKey, string>> = {
  '24h': 'últimas 24 horas',
  '7d': 'últimos 7 días',
  '30d': 'últimos 30 días',
  '90d': 'últimos 90 días',
}

export function isWindowKey(value: string): value is WindowKey {
  return (WINDOW_KEYS as readonly string[]).includes(value)
}

export const DESKTOP_STRIP_DAYS = 90
export const MOBILE_STRIP_DAYS = 30
export const DAY_BUCKETS_24H = 48
