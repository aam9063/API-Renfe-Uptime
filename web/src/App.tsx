import { Methodology } from './features/methodology'
import { ServiceDetail } from './features/service-detail'
import { StatusOverview } from './features/status-overview'
import { Shell } from './ui/Shell'
import { Link, useRouteLocation } from './ui/router'

const ROUTE_TITLES: ReadonlyArray<[RegExp, string]> = [
  [/^\/servicio\/[^/]+$/, 'Nueves, detalle de servicio'],
  [/^\/metodologia$/, 'Nueves, metodología'],
  [/^\/$/, 'Nueves, inicio'],
]

function routeTitle(path: string): string {
  for (const [pattern, title] of ROUTE_TITLES) {
    if (pattern.test(path)) {
      return title
    }
  }
  return 'Nueves, página no encontrada'
}

export function App() {
  const { path } = useRouteLocation()
  const detailMatch = /^\/servicio\/([^/]+)$/.exec(path)
  document.title = routeTitle(path)

  return (
    <Shell>
      {path === '/' && <StatusOverview />}
      {path === '/metodologia' && <Methodology />}
      {detailMatch !== null && detailMatch[1] !== undefined && (
        <ServiceDetail probeId={decodeURIComponent(detailMatch[1])} />
      )}
      {path !== '/' && path !== '/metodologia' && detailMatch === null && <NotFound />}
    </Shell>
  )
}

function NotFound() {
  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-line bg-surface p-8">
      <h1 className="m-0 font-display text-[28px] font-bold">Página no encontrada</h1>
      <p className="m-0 text-[15px] leading-relaxed text-ink-soft">
        La página que buscas no existe. Vuelve a{' '}
        <Link to="/" className="text-link hover:text-ink">Estado</Link> o consulta la{' '}
        <Link to="/metodologia" className="text-link hover:text-ink">metodología</Link>.
      </p>
    </section>
  )
}
