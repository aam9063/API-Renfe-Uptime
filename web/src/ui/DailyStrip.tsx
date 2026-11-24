import type { Daily90Row } from '../data/hooks'

import { dailyBarClass } from './outcome'

// The day strip: one bar per day, oldest on the left. Days the view has no
// answer for read as "sin datos".

export function DailyStrip({
  days,
  label,
  rows,
  className,
}: {
  days: number
  label: string
  rows: readonly Daily90Row[]
  className?: string
}) {
  const visible = rows.length > days ? rows.slice(rows.length - days) : [...rows]
  const missing = days - visible.length
  return (
    <div
      role="img"
      aria-label={label}
      className={`flex gap-[2px] ${className ?? 'h-[22px] md:h-[30px]'}`}
    >
      {Array.from({ length: missing }, (_, missingIndex) => (
        <span
          key={`sin-datos-${missingIndex}`}
          className="min-w-[2px] flex-1 rounded-[2px] bg-nodata"
        />
      ))}
      {visible.map((row) => (
        <span
          key={row.day}
          className={`min-w-[2px] flex-1 rounded-[2px] ${dailyBarClass(row.worst_outcome)}`}
        />
      ))}
    </div>
  )
}
