export function ServiceDetail({ probeId }: { probeId: string }) {
  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-line bg-surface p-8">
      <h1 className="m-0 font-display text-[28px] font-bold">Detalle del servicio</h1>
      <p className="m-0 font-mono text-[14px] text-muted">{probeId}</p>
    </section>
  )
}
