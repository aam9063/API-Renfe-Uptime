import { isConfigured } from '../../data/client'
import { useIncidents, useStatusNow } from '../../data/hooks'
import { ErrorState, LoadingState, NoDataState } from '../../ui/states'
import { buildIncidents, IncidentCard } from './IncidentData'

export function IncidentsList() {
  const incidents = useIncidents()
  const statusNow = useStatusNow()

  if (incidents.isError || statusNow.isError) {
    return (
      <ErrorState
        onRetry={() => {
          void incidents.refetch()
          void statusNow.refetch()
        }}
      />
    )
  }
  if (!isConfigured) {
    return <NoDataState />
  }
  if (incidents.isPending) {
    return <LoadingState />
  }

  const items = buildIncidents(
    incidents.data ?? [],
    statusNow.data ?? [],
    new Date().toISOString(),
  )
  return (
    <section id="incidentes" aria-labelledby="incidentes-title" className="flex flex-col gap-4">
      <h2 id="incidentes-title" className="m-0 font-display text-[18px] font-bold md:text-[22px]">
        Incidentes recientes
      </h2>
      {items.length === 0 ? (
        <p className="m-0 text-[15px] text-muted">Sin incidentes todavía.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((incident) => (
            <IncidentCard key={`${incident.probeId}-${incident.when}`} incident={incident} />
          ))}
        </div>
      )}
    </section>
  )
}
