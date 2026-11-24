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

function log10Of(value: bigint): number {
  const digits = value.toString()
  const head = digits.slice(0, 17)
  return digits.length - head.length + Math.log10(Number(head))
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
    nines:
      downSum === 0n
        ? null
        : Math.max(0, Math.floor(log10Of(meanDenominator) - log10Of(downSum))),
    downSeconds,
  }
}
