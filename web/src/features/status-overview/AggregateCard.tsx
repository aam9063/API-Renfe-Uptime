import type { UptimeWindowRow } from '../../data/hooks'
import { WINDOW_LONG_LABELS, WINDOW_KEYS, type WindowKey } from '../../lib/windows'
import { displayPercent, formatDuration, ninesText } from '../../lib/format'
import { aggregateWindows } from '../../lib/windowAggregate'

const SAMPLE_INTRO =
  'Un SaaS serio presume de 99,99 % (4 nueves): menos de 5 minutos caído al mes. Aquí medimos los servicios de Renfe con el mismo listón, desde fuera, como los ve cualquier usuario.'

export function AggregateCard({
  windowRows,
  selected,
  onSelect,
}: {
  windowRows: readonly UptimeWindowRow[]
  selected: WindowKey
  onSelect: (key: WindowKey) => void
}) {
  const aggregate = aggregateWindows(windowRows, selected)
  const percent = displayPercent(aggregate.uptime)
  const label = WINDOW_LONG_LABELS[selected]

  return (
    <div className="flex min-w-[280px] flex-1 flex-col gap-6 rounded-2xl border border-line bg-surface p-5 md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="m-0 font-display text-[22px] font-bold md:text-[28px]">
          ¿Cuántos nueves tiene Renfe?
        </h1>
        <div role="tablist" aria-label="Ventana de tiempo" className="flex gap-1 rounded-[10px] bg-chip p-1">
          {WINDOW_KEYS.map((key) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={key === selected}
              onClick={() => onSelect(key)}
              className={
                key === selected
                  ? 'min-h-10 rounded-lg bg-panel px-3.5 text-[14px] font-semibold text-surface'
                  : 'min-h-10 rounded-lg bg-transparent px-3.5 text-[14px] font-semibold text-ink-soft'
              }
            >
              {key}
            </button>
          ))}
        </div>
      </div>
      <div className="flex flex-wrap items-end gap-x-10 gap-y-4">
        <div>
          <div className="font-mono text-[72px] font-semibold leading-none tracking-[-3px] md:text-[112px] md:tracking-[-4px]">
            {percent ?? 'Sin datos'}
            {percent !== null && <span className="text-[32px] tracking-normal md:text-[48px]">%</span>}
          </div>
          <div className="mt-2 text-[15px] text-muted">Uptime agregado de las APIs, {label}</div>
        </div>
        {aggregate.serviceCount > 0 && (
          <div className="flex flex-col gap-2 pb-3">
            <span className="font-display text-[26px] font-bold md:text-[40px]">
              {ninesText(aggregate.nines, { insufficient: false })}
            </span>
            <span className="text-[14px] text-muted md:text-[15px]">
              {formatDuration(aggregate.downSeconds)} caído en total
            </span>
          </div>
        )}
      </div>
      <p className="m-0 max-w-[640px] text-[15px] leading-relaxed text-ink-soft">{SAMPLE_INTRO}</p>
    </div>
  )
}
