// Formatting of the numbers the views publish. The web never computes uptime or
// nines: `v_uptime_windows`, `v_daily_90` and the other views do. This module
// truncates, adds the Spanish comma and chooses the labels, following
// `contracts/uptime_cases.json` as the shared truth.

const PERCENT_STEP_UNITS = 10000

type Ratio = {
  numerator: bigint
  denominator: bigint
}

function isDigits(text: string): boolean {
  return /^\d+$/.test(text)
}

function decimalExponent(digits: string): Ratio | null {
  const dot = digits.indexOf('.')
  if (dot < 0) {
    return isDigits(digits) ? { numerator: BigInt(digits), denominator: 1n } : null
  }
  const integerPart = dot === 0 ? '0' : digits.slice(0, dot)
  const fractionalPart = digits.slice(dot + 1)
  if (!isDigits(integerPart) || !isDigits(fractionalPart) || fractionalPart === '') {
    return null
  }
  return {
    numerator: BigInt(integerPart + fractionalPart),
    denominator: 10n ** BigInt(fractionalPart.length),
  }
}

function parseRatio(text: string | null): Ratio | null {
  if (text === null) {
    return null
  }
  const value = text.trim()
  const slash = value.indexOf('/')
  if (slash < 0) {
    return decimalExponent(value)
  }
  const numerator = value.slice(0, slash)
  const denominator = value.slice(slash + 1)
  if (!isDigits(numerator) || !isDigits(denominator)) {
    return null
  }
  const denominatorValue = BigInt(denominator)
  if (denominatorValue === 0n) {
    return null
  }
  return { numerator: BigInt(numerator), denominator: denominatorValue }
}

/**
 * Two decimals, truncated, with the Spanish comma: the same contract the SQL
 * views follow. Accepts an exact fraction (`99996/100000`) or the numeric
 * uptime of a view (`0.99996`), always as text to keep the truncation exact.
 */
export function displayPercent(uptime: string | null): string | null {
  const ratio = parseRatio(uptime)
  if (ratio === null) {
    return null
  }
  const scaled = (ratio.numerator * BigInt(PERCENT_STEP_UNITS)) / ratio.denominator
  const integerPart = scaled / 100n
  const fractionalPart = scaled % 100n
  return `${integerPart.toString()},${fractionalPart.toString().padStart(2, '0')}`
}

export type WindowFlags = {
  insufficient: boolean
  noDowntime: boolean
}

/** The human label of an uptime window: nothing when the percent speaks alone. */
export function windowLabel(flags: WindowFlags): string | null {
  if (flags.insufficient) {
    return 'datos insuficientes'
  }
  if (flags.noDowntime) {
    return 'sin caídas'
  }
  return null
}

export type NinesFlags = {
  insufficient: boolean
}

/** "3 nueves", and "sin caídas" instead of infinite nines. */
export function ninesText(nines: number | null, flags: NinesFlags): string {
  if (flags.insufficient) {
    return 'datos insuficientes'
  }
  if (nines === null) {
    return 'sin caídas'
  }
  if (nines === 1) {
    return '1 nueve'
  }
  return `${nines} nueves`
}

/** Duration the way the design reads it: 26 s, 38 min, 4 min 23 s, 2 h 14 min. */
export function formatDuration(seconds: number): string {
  if (seconds <= 0) {
    return '0 s'
  }
  if (seconds < 60) {
    return `${seconds} s`
  }
  const hours = Math.floor(seconds / 3600)
  if (hours === 0) {
    const minutes = Math.floor(seconds / 60)
    const rest = seconds % 60
    return rest === 0 ? `${minutes} min` : `${minutes} min ${rest} s`
  }
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours} h ${minutes.toString().padStart(2, '0')} min`
}

/** Latency the way the design reads it: 318 ms, 1,4 s, 2,31 s. */
export function formatLatency(millis: number | null): string {
  if (millis === null || millis <= 0) {
    return 'n/d'
  }
  if (millis < 1000) {
    return `${millis} ms`
  }
  const seconds = millis / 1000
  const trimmed = seconds.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
  return `${trimmed.replace('.', ',')} s`
}

/** A past instant the way the design reads it: hace 23 s, hace 4 días. */
export function formatRelative(iso: string, nowIso: string): string {
  const diffSeconds = Math.round((Date.parse(nowIso) - Date.parse(iso)) / 1000)
  if (diffSeconds <= 0) {
    return 'ahora'
  }
  if (diffSeconds < 60) {
    return `hace ${diffSeconds} s`
  }
  if (diffSeconds < 3600) {
    return `hace ${Math.floor(diffSeconds / 60)} min`
  }
  if (diffSeconds < 86400) {
    return `hace ${Math.floor(diffSeconds / 3600)} h`
  }
  return `hace ${Math.floor(diffSeconds / 86400)} días`
}

function formatDate(iso: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat('es-ES', options).format(new Date(iso))
}

/** "16:38:12", in the local time zone of the browser. */
export function formatClock(iso: string): string {
  return formatDate(iso, { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

/** "26 ago", or "25 ene 2027" when the year is asked for. */
export function formatDay(iso: string): string {
  return formatDate(iso, { day: 'numeric', month: 'short' })
}

export function formatDateWithYear(iso: string): string {
  return formatDate(iso, { day: 'numeric', month: 'short', year: 'numeric' })
}

/** The catalog intervals: 60 s becomes "1 min", 900 s becomes "15 min". */
export function formatInterval(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} s`
  }
  const rest = seconds % 60
  if (rest === 0) {
    return `${seconds / 60} min`
  }
  return formatDuration(seconds)
}
