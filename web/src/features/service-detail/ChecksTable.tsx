import type { RecentCheckRow } from '../../data/hooks'

import { checkBadge } from '../../ui/outcome'
import { formatClock, formatLatency } from '../../lib/format'

// The recent checks table. The views publish what was checked, when and how
// long it took; there is no per check reason column in the view contract, so
// the table shows exactly what was measured.

export function ChecksTable({ rows }: { rows: readonly RecentCheckRow[] }) {
  return (
    <div className="flex min-w-0 flex-[2_1_520px] flex-col gap-3 rounded-2xl border border-line bg-surface p-5 md:p-6">
      <h2 className="m-0 font-display text-[20px] font-bold">Últimas comprobaciones</h2>
      {rows.length === 0 ? (
        <p className="m-0 text-[14px] text-muted">Aún no hay comprobaciones registradas.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[420px] border-collapse text-[14px]">
            <thead>
              <tr className="text-left text-[12px] text-muted">
                <th className="pl-0 p-2 pb-2 pt-2 font-semibold">Hora</th>
                <th className="p-2 font-semibold">Resultado</th>
                <th className="p-2 font-semibold">HTTP</th>
                <th className="p-2 font-semibold">Latencia</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${row.started_at}-${index}`} className="border-t border-line-soft">
                  <td className="p-2.5 font-mono">{formatClock(row.started_at)}</td>
                  <td className="p-2.5">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[12px] font-semibold ${checkBadge(row.outcome).className}`}
                    >
                      {checkBadge(row.outcome).label}
                    </span>
                  </td>
                  <td className="p-2.5 font-mono">{row.http_status ?? 'n/d'}</td>
                  <td className="p-2.5 font-mono">{formatLatency(row.duration_ms)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
