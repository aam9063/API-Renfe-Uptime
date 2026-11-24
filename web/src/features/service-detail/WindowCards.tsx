import { formatDuration, ninesText } from '../../lib/format'

export type WindowCardRow = {
  window_label: string
  display_percent: string | null
  nines: number | null
  insufficient: boolean
  no_downtime: boolean
  down_seconds: number
}

export function WindowCards({ rows }: { rows: readonly WindowCardRow[] }) {
  return (
    <section aria-label="Uptime por ventana" className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {rows.map((row) => (
        <div
          key={row.window_label}
          className="flex min-w-0 flex-col gap-1.5 rounded-2xl border border-line bg-surface p-5"
        >
          <span className="text-[13px] text-muted">{row.window_label}</span>
          <span className="font-mono text-[22px] font-semibold md:text-[30px]">
            {row.display_percent ?? 'Sin datos'}
            {row.display_percent !== null ? ' %' : ''}
          </span>
          <span className="font-display text-[15px] font-bold">
            {ninesText(row.nines, { insufficient: row.insufficient })}
          </span>
          <span className="text-[13px] text-muted">{formatDuration(row.down_seconds)} caído</span>
        </div>
      ))}
    </section>
  )
}
