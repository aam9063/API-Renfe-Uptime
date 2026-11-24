import type { ServiceGroupItem } from './OverviewData'
import { DESKTOP_STRIP_DAYS, MOBILE_STRIP_DAYS } from '../../lib/windows'
import { Link } from '../../ui/router'
import { legendChip } from '../../ui/outcome'
import { ninesText, formatRelative } from '../../lib/format'
import { DailyStrip } from './DailyStrip'

const LEGEND_OUTCOMES = ['up', 'degraded', 'down', 'blocked', 'unknown'] as const

function serviceNowLabel(lastCheckAt: string | null): string {
  if (lastCheckAt === null) {
    return 'sin comprobar todavía'
  }
  return formatRelative(lastCheckAt, new Date().toISOString())
}

export function ServiceGroups({ groups }: { groups: readonly ServiceGroupItem[] }) {
  return (
    <section aria-labelledby="servicios" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 id="servicios" className="m-0 font-display text-[18px] md:text-[22px]">
          Servicios
        </h2>
        <div className="flex flex-wrap gap-4 text-[13px] text-ink-soft">
          {LEGEND_OUTCOMES.map((outcome) => (
            <span key={outcome} className="flex items-center gap-1.5">
              <span className={`size-2.5 rounded-[2px] ${legendChip(outcome).className}`} />
              {legendChip(outcome).label}
            </span>
          ))}
        </div>
      </div>

      {groups.map((group) => (
        <div key={group.name} className="overflow-hidden rounded-2xl border border-line bg-surface">
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2 border-b border-line bg-canvas px-5 py-3.5 md:px-6">
            <h3 className="m-0 text-[15px] font-semibold">{group.name}</h3>
            <span className="font-mono text-[13px] text-muted">{group.host}</span>
            {group.retirementNote !== null && (
              <span className="rounded-md bg-warn-surface px-2 py-0.5 text-[12px] font-semibold text-warn-ink">
                {group.retirementNote}
              </span>
            )}
          </div>

          {group.services.map((service) => (
            <div
              key={service.probeId}
              className="border-t border-line-soft first:border-t-0"
            >
              <Link
                to={`/servicio/${encodeURIComponent(service.probeId)}`}
                className="block px-5 py-4 no-underline md:px-6 md:py-4.5"
              >
                <div className="hidden flex-wrap items-center gap-x-8 gap-y-3 md:flex">
                  <div className="min-w-0 flex-[1_1_220px]">
                    <div className="text-[15px] font-semibold text-ink">{service.name}</div>
                    <div className="mt-1 font-mono text-[12px] text-muted">
                      {service.checkLine} · {serviceNowLabel(service.lastCheckAt)}
                    </div>
                  </div>
                  <div className="flex gap-6">
                    <div className="text-right">
                      <div className="font-mono text-[15px] font-semibold">
                        {service.displayPercent ?? 'Sin datos'} %
                      </div>
                      <div className="text-[12px] text-muted">30 días</div>
                    </div>
                    <div className="min-w-[76px] text-right">
                      <div className="font-display text-[15px] font-bold">
                        {ninesText(service.nines, {
                          insufficient: service.insufficient,
                        })}
                      </div>
                      <div className="text-[12px] text-muted">p95 {service.p95}</div>
                    </div>
                  </div>
                  <DailyStrip
                    days={DESKTOP_STRIP_DAYS}
                    rows={service.daily}
                    label={`${service.name}: estado diario de los últimos 90 días`}
                    className="h-[30px] flex-[1_1_420px]"
                  />
                </div>

                <div className="flex flex-col gap-2.5 md:hidden">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-[15px] font-semibold text-ink">{service.name}</span>
                    <span className="whitespace-nowrap font-mono text-[14px] font-semibold">
                      {service.displayPercent ?? 'Sin datos'} %
                    </span>
                  </div>
                  <DailyStrip
                    days={MOBILE_STRIP_DAYS}
                    rows={service.daily}
                    label={`${service.name}: estado diario de los últimos 30 días`}
                    className="h-[22px]"
                  />
                  <span className="text-[13px] text-muted">
                    {ninesText(service.nines, {
                      insufficient: service.insufficient,
                    })}{' '}
                    · p95 {service.p95}
                  </span>
                </div>
              </Link>
            </div>
          ))}
        </div>
      ))}

      <div className="flex justify-between text-[12px] text-muted">
        <span>hace 90 días</span>
        <span>hoy</span>
      </div>
    </section>
  )
}
