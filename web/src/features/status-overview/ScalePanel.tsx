import { Link } from '../../ui/router'

const SCALE_ROWS = [
  { pct: '99 %', label: '2 nueves', down: '7 h 18 min' },
  { pct: '99,9 %', label: '3 nueves', down: '43 min' },
  { pct: '99,99 %', label: '4 nueves', down: '4 min 23 s' },
  { pct: '99,999 %', label: '5 nueves', down: '26 s' },
]

export function ScalePanel() {
  return (
    <aside
      aria-label="Escala de nueves"
      className="flex min-w-[280px] flex-1 basis-[300px] flex-col gap-4 rounded-2xl bg-panel p-7 text-surface"
    >
      <h2 className="m-0 font-display text-[18px] font-bold">La escala</h2>
      {SCALE_ROWS.map((row) => (
        <div
          key={row.pct}
          className="flex justify-between gap-3 border-b border-panel-line pb-3 text-[14px]"
        >
          <span className="font-mono">{row.pct}</span>
          <span className="text-panel-muted">{row.label}</span>
          <span className="font-mono">{row.down}/mes</span>
        </div>
      ))}
      <Link to="/metodologia" className="text-[14px] font-medium text-link-dark">
        Cómo lo calculamos →
      </Link>
    </aside>
  )
}
