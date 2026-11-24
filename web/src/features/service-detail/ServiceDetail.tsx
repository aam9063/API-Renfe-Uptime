import { isConfigured } from '../../data/client'
import {
  useDaily90,
  useLatency24h,
  useProbes,
  useRecentChecks,
  useStatusNow,
  useUptimeWindows,
} from '../../data/hooks'
import { DailyStrip } from '../../ui/DailyStrip'
import { ErrorState, LoadingState, NoDataState } from '../../ui/states'
import { statusDotClass, statusPill } from '../../ui/outcome'
import { formatDateWithYear, formatRelative } from '../../lib/format'
import { DESKTOP_STRIP_DAYS, WINDOW_KEYS } from '../../lib/windows'
import { Link } from '../../ui/router'
import { ChecksTable } from './ChecksTable'
import { LatencyPanel } from './LatencyPanel'
import { ProbeRules } from './ProbeRules'
import { WindowCards } from './WindowCards'

export function ServiceDetail({ probeId }: { probeId: string }) {
  const statusNow = useStatusNow()
  const windows = useUptimeWindows()
  const daily = useDaily90()
  const latency = useLatency24h()
  const checks = useRecentChecks(probeId)
  const probes = useProbes()
  const queries = [statusNow, windows, daily, latency, checks, probes]

  if (queries.some((query) => query.isError)) {
    return <ErrorState onRetry={() => queries.forEach((query) => void query.refetch())} />
  }
  if (!isConfigured) {
    return <NoDataState />
  }
  if (queries.some((query) => query.isPending)) {
    return <LoadingState />
  }

  const status = statusNow.data?.find((row) => row.probe_id === probeId) ?? null
  const probe = probes.data?.find((row) => row.id === probeId) ?? null
  if (status === null) {
    return <NoDataState label="Servicio no encontrado" />
  }

  const windowRows = WINDOW_KEYS.flatMap((key) => {
    const row = (windows.data ?? []).find(
      (candidate) => candidate.probe_id === probeId && candidate.window_key === key,
    )
    return row === undefined ? [] : [row]
  })
  const dailyRows = (daily.data ?? []).filter((row) => row.probe_id === probeId)
  const latencyRows = (latency.data ?? []).filter((row) => row.probe_id === probeId)
  const pill = statusPill(status.outcome)

  return (
    <>
      <nav aria-label="Ruta" className="flex gap-2 text-[14px] text-muted">
        <Link to="/" className="text-muted hover:text-ink">
          Estado
        </Link>
        <span aria-hidden="true">/</span>
        <span>{status.group_name}</span>
        <span aria-hidden="true">/</span>
        <span className="text-ink">{status.name}</span>
      </nav>

      <section className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 className="m-0 font-display text-[36px] font-bold">{status.name}</h1>
          <span className="font-mono text-[14px] text-muted">
            {probe === null ? status.host : `${probe.method} ${probe.url_display}`}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`flex items-center gap-2 rounded-full px-3.5 py-2 text-[15px] font-semibold ${pill.className}`}
          >
            <span className={`size-2.5 rounded-full ${statusDotClass(status.outcome)}`} />
            {pill.label} ahora
          </span>
          <span className="text-[13px] text-muted">
            {status.last_check_at === null
              ? 'sin comprobaciones todavía'
              : `última sonda ${formatRelative(status.last_check_at, new Date().toISOString())}`}
          </span>
        </div>
      </section>

      {probe !== null && probe.retired_at !== null && (
        <aside className="rounded-2xl border border-line bg-warn-surface px-5 py-4 text-[14px] font-semibold text-warn-ink">
          Servicio en retirada: la venta nueva le sustituye y deja de medirse el{' '}
          {formatDateWithYear(probe.retired_at)}.
        </aside>
      )}

      <WindowCards rows={windowRows} />
      <LatencyPanel rows={latencyRows} degradedMs={probe?.degraded_ms ?? null} />

      <section
        aria-labelledby="dias"
        className="flex flex-col gap-3 rounded-2xl border border-line bg-surface p-5 md:p-6"
      >
        <h2 id="dias" className="m-0 font-display text-[20px] font-bold">
          Últimos 90 días
        </h2>
        <DailyStrip
          days={DESKTOP_STRIP_DAYS}
          rows={dailyRows}
          label={`Estado diario de los últimos 90 días de ${status.name}`}
          className="h-[44px]"
        />
        <div className="flex justify-between text-[12px] text-muted">
          <span>hace 90 días</span>
          <span>hoy</span>
        </div>
      </section>

      <section className="flex flex-wrap items-start gap-6">
        <div className="min-w-[280px] flex-[1_1_360px]">
          <ProbeRules probe={probe} />
        </div>
        <ChecksTable rows={checks.data ?? []} />
      </section>
    </>
  )
}
