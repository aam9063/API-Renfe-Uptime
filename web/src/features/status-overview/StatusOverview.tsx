import { useState } from 'react'

import { isConfigured } from '../../data/client'
import {
  useDaily90,
  useLatency24h,
  useProbes,
  useStatusNow,
  useUptimeWindows,
} from '../../data/hooks'
import { ErrorState, LoadingState, NoDataState } from '../../ui/states'
import type { WindowKey } from '../../lib/windows'
import { IncidentsList } from '../incidents'
import { AggregateCard } from './AggregateCard'
import { ScalePanel } from './ScalePanel'
import { ServiceGroups } from './ServiceGroups'
import { buildOverview } from './OverviewData'

export function StatusOverview() {
  const [windowKey, setWindowKey] = useState<WindowKey>('30d')
  const statusNow = useStatusNow()
  const windows = useUptimeWindows()
  const daily = useDaily90()
  const latency = useLatency24h()
  const probes = useProbes()
  const queries = [statusNow, windows, daily, latency, probes]

  if (queries.some((query) => query.isError)) {
    return (
      <ErrorState onRetry={() => queries.forEach((query) => void query.refetch())} />
    )
  }
  if (!isConfigured) {
    return <NoDataState />
  }
  if (queries.some((query) => query.isPending)) {
    return <LoadingState />
  }
  if (statusNow.data?.length === 0) {
    return <NoDataState />
  }

  const overview = buildOverview({
    statusRows: statusNow.data ?? [],
    windowRows: windows.data ?? [],
    dailyRows: daily.data ?? [],
    latencyRows: latency.data ?? [],
    probeRows: probes.data ?? [],
    windowKey,
  })

  return (
    <>
      <section className="flex flex-wrap items-stretch gap-5 md:gap-8">
        <AggregateCard
          windowRows={windows.data ?? []}
          selected={windowKey}
          onSelect={setWindowKey}
        />
        <ScalePanel />
      </section>
      <ServiceGroups groups={overview.groups} />
      <IncidentsList />
    </>
  )
}
