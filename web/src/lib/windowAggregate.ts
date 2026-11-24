import type { UptimeWindowRow } from '../data/hooks'

// The aggregate of the home page: the unweighted mean of the services that
// have data for the window, as the feature map defines it. A service without
// data is excluded, never counted as down. The mean is computed with exact
// BigInt fractions and formatted through the shared truncation.

export type WindowAggregate = {
  serviceCount: number
  uptime: string | null
  nines: number | null
  downSeconds: number
}

const MAX_NINES = 12n

// Exact integer nines: the largest n with 10^n * down <= denominator, the same
// rule as the SQL views and the Python domain. A float log10 lands on
// 2.9999999 for an exact 1000x ratio and publishes one nine too few.
function ninesOf(denominator: bigint, down: bigint): number | null {
  if (down <= 0n) {
    return null
  }
  let nines = 0n
  let scale = 10n
  while (nines < MAX_NINES && scale * down <= denominator) {
    nines += 1n
    scale *= 10n
  }
  return Number(nines)
}

function gcd(a: bigint, b: bigint): bigint {
  let first = a
  let second = b
  while (second !== 0n) {
    const rest = first % second
    first = second
    second = rest
  }
  return first
}

export function aggregateWindows(
  rows: readonly UptimeWindowRow[],
  windowKey: string,
): WindowAggregate {
  const windowRows = rows.filter(
    (row) => row.window_key === windowKey && row.denominator_seconds > 0,
  )
  if (windowRows.length === 0) {
    return { serviceCount: 0, uptime: null, nines: null, downSeconds: 0 }
  }
  const commonDenominator = windowRows.reduce(
    (acc, row) => acc * BigInt(row.denominator_seconds),
    1n,
  )
  const count = BigInt(windowRows.length)
  let availableSum = 0n
  let downSum = 0n
  let downSeconds = 0
  for (const row of windowRows) {
    const denominator = BigInt(row.denominator_seconds)
    const down = BigInt(row.down_seconds)
    const weight = commonDenominator / denominator
    availableSum += (denominator - down) * weight
    downSum += down * weight
    downSeconds += row.down_seconds
  }
  const meanDenominator = commonDenominator * count
  const divisor = gcd(availableSum, meanDenominator)
  return {
    serviceCount: windowRows.length,
    uptime:
      divisor === 0n
        ? null
        : `${availableSum / divisor}/${meanDenominator / divisor}`,
    nines: ninesOf(meanDenominator, downSum),
    downSeconds,
  }
}
