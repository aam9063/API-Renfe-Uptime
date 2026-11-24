import { useState } from 'react'

import type { Latency24hRow } from '../../data/hooks'
import { DAY_BUCKETS_24H } from '../../lib/windows'
import { buildLatencyBars, midpointOf } from '../../lib/latencyBars'
import { formatLatency } from '../../lib/format'

const METRICS = ['p50', 'p95'] as const

export type Metric = (typeof METRICS)[number]

export function LatencyPanel({
  rows,
  degradedMs,
}: {
  rows: readonly Latency24hRow[]
  degradedMs: number | null
}) {
  const [metric, setMetric] = useState<Metric>('p50')
  const buckets = rows.slice(Math.max(0, rows.length - DAY_BUCKETS_24H))
  const values = buckets.map((row) => (metric === 'p50' ? row.p50_ms : row.p95_ms))
  const threshold = degradedMs ?? 0
  const bars = buildLatencyBars(values, threshold)
  const latest = buckets.length === 0 ? null : (buckets[buckets.length - 1] ?? null)

  return (
    <section
      aria-labelledby="latencia"
      className="flex flex-col gap-4 rounded-2xl border border-line bg-surface p-5 md:p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="latencia" className="m-0 font-display text-[20px] font-bold">
          Latencia, últimas 24 h
        </h2>
        <div role="tablist" aria-label="Métrica" className="flex gap-1 rounded-[10px] bg-chip p-1">
          {METRICS.map((candidate) => (
            <button
              key={candidate}
              type="button"
              role="tab"
              aria-selected={candidate === metric}
              onClick={() => setMetric(candidate)}
              className={
                candidate === metric
                  ? 'min-h-10 rounded-lg bg-panel px-3.5 text-[14px] font-semibold text-surface'
                  : 'min-h-10 rounded-lg bg-transparent px-3.5 text-[14px] font-semibold text-ink-soft'
              }
            >
              {candidate}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <div
          aria-hidden="true"
          className="flex h-[200px] flex-col justify-between text-right font-mono text-[12px] text-muted"
        >
          <span>{formatLatency(threshold)}</span>
          <span>{formatLatency(midpointOf(threshold))}</span>
          <span>0</span>
        </div>
        <div
          role="img"
          aria-label={`Latencia ${metric} cada 30 minutos en las últimas 24 horas`}
          className="flex h-[200px] flex-1 items-end gap-[3px] border-b border-line-strong"
        >
          {bars.map((bar, index) => (
            <span
              key={`bucket-${index}`}
              className={`min-w-[3px] flex-1 rounded-t-[2px] ${bar.className}`}
              style={{ height: `${bar.heightPercent}%` }}
            />
          ))}
        </div>
      </div>
      <div className="flex justify-between pl-11 text-[12px] text-muted">
        <span>hace 24 h</span>
        <span>hace 12 h</span>
        <span>ahora</span>
      </div>
      <div className="flex flex-wrap gap-6 text-[13px] text-ink-soft">
        <span>
          p50 <b className="font-mono">{formatLatency(latest?.p50_ms ?? null)}</b>
        </span>
        <span>
          p95 <b className="font-mono">{formatLatency(latest?.p95_ms ?? null)}</b>
        </span>
        <span>
          Umbral de degradado <b className="font-mono">{formatLatency(degradedMs)}</b>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-[2px] bg-down" />
          sin respuesta
        </span>
      </div>
    </section>
  )
}
