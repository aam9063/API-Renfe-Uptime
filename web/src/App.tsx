import { OfficialNotice } from './ui/OfficialNotice'

export function App() {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-4 px-8 py-4">
          <span className="flex items-center gap-2.5">
            <span className="flex size-9 items-center justify-center rounded-lg bg-ink font-mono text-base font-semibold text-surface">
              A9
            </span>
            <span className="font-display text-[22px] font-bold">Andén 9</span>
          </span>
          <OfficialNotice />
        </div>
      </header>
      <main className="mx-auto flex max-w-[1200px] flex-col gap-6 px-8 py-10">
        <h1 className="font-display text-[28px] font-bold">
          Andamio listo, las pantallas llegan en M4
        </h1>
        <p className="max-w-[640px] text-[15px] leading-relaxed text-ink-soft">
          Este repositorio mide el uptime de las APIs de Renfe con la sonda y publica los
          agregados desde Supabase. La web solo formatea.
        </p>
      </main>
    </div>
  )
}
