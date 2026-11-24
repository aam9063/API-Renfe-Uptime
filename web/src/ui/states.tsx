// Loading, error and "sin datos" states shared by every screen. A missing
// configuration is a state, not a crash.

export function LoadingState() {
  return (
    <div
      role="status"
      className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-8 text-[15px] text-muted"
    >
      <span className="font-display text-[18px] font-bold text-ink">Cargando…</span>
      <span> Consultando las vistas de la base de datos.</span>
    </div>
  )
}

export function NoDataState({ label = 'Sin datos' }: { label?: string }) {
  return (
    <div
      role="status"
      className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-8 text-[15px] text-muted"
    >
      <span className="font-display text-[18px] font-bold text-ink">{label}</span>
      <span>
        La sonda todavía no ha medido lo suficiente en esta ventana, o la web no puede alcanzar la
        base de datos.
      </span>
    </div>
  )
}

export function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-line bg-surface p-8"
    >
      <div className="flex flex-col gap-2 text-[15px] text-muted">
        <span className="font-display text-[18px] font-bold text-ink">
          No pudimos cargar los datos
        </span>
        <span> Las vistas no respondieron. Puedes volver a intentarlo.</span>
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="rounded-lg bg-panel px-4 py-2.5 text-[14px] font-semibold text-surface hover:opacity-90"
      >
        Reintentar
      </button>
    </div>
  )
}
