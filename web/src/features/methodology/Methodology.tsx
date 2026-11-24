import { isConfigured } from '../../data/client'
import { useProbes, type ProbeRow } from '../../data/hooks'
import { formatInterval } from '../../lib/format'

export function ProbeCatalog({ probes }: { probes: readonly ProbeRow[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
      <table className="w-full min-w-[560px] border-collapse text-[14px]">
        <thead>
          <tr className="text-left text-[12px] text-muted">
            <th className="bg-canvas p-3 md:px-6 font-semibold">Servicio</th>
            <th className="bg-canvas p-3 font-semibold">Endpoint</th>
            <th className="bg-canvas p-3 md:pr-6 font-semibold">Cada</th>
          </tr>
        </thead>
        <tbody>
          {probes.map((probe) => (
            <tr key={probe.id} className="border-t border-line-soft">
              <td className="p-3 font-semibold md:px-6">{probe.name}</td>
              <td className="p-3 font-mono text-[12px] text-ink-soft">
                {probe.method} {probe.url_display}
              </td>
              <td className="p-3 font-mono md:pr-6">{formatInterval(probe.interval_s)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Methodology() {
  const catalog = useProbes()

  return (
    <main className="mx-auto flex max-w-[960px] flex-col gap-10 px-5 py-12 md:px-8 md:py-18">
      <div className="flex flex-col gap-3">
        <h1 className="m-0 font-display text-[44px] font-bold leading-tight">Cómo medimos</h1>
        <p className="m-0 text-[18px] leading-relaxed text-ink-soft">
          Una sonda llama a los mismos servicios que usa renfe-cli, cada pocos minutos, y anota si
          respondieron bien. Con eso calculamos el uptime y lo traducimos a nueves, igual que hace
          cualquier status page de un SaaS.
        </p>
      </div>

      <section aria-labelledby="estados" className="flex flex-col gap-4">
        <h2 id="estados" className="m-0 font-display text-[24px] font-bold">
          Los cinco estados
        </h2>
        <div className="overflow-hidden rounded-2xl border border-line bg-surface">
          {STATES.map((state) => (
            <div
              key={state.name}
              className="flex flex-wrap items-baseline gap-x-6 gap-y-2 border-t border-line-soft px-5 py-4.5 first:border-t-0 md:px-6"
            >
              <span className="flex flex-[0_0_160px] items-center gap-2 font-semibold">
                <span className={`size-3 rounded-[3px] ${state.dot}`} />
                {state.name}
              </span>
              <span className="flex-[1_1_360px] text-[15px] leading-relaxed text-ink-soft">
                {state.text}
              </span>
              <span
                className={`rounded-full px-2.5 py-0.5 text-[12px] font-semibold ${state.badge}`}
              >
                {state.count}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="formula" className="flex flex-wrap gap-6">
        <div className="flex min-w-[280px] flex-[1_1_400px] flex-col gap-3">
          <h2 id="formula" className="m-0 font-display text-[24px] font-bold">
            La fórmula
          </h2>
          <p className="m-0 text-[15px] leading-relaxed text-ink-soft">
            Cada comprobación cubre su intervalo. Los minutos bloqueados o sin datos salen del
            denominador: no sabemos qué vio un usuario normal, así que no los contamos ni a favor
            ni en contra.
          </p>
          <p className="m-0 text-[15px] leading-relaxed text-ink-soft">
            Un incidente se abre tras 2 fallos seguidos y se cierra tras 2 éxitos seguidos. La
            duración cuenta desde el primer fallo.
          </p>
        </div>
        <div className="flex min-w-[280px] flex-[1_1_400px] flex-col gap-4 rounded-2xl bg-panel p-7 font-mono text-[15px] leading-relaxed text-surface">
          <div>
            <span className="text-panel-muted">uptime =</span>
            <br />
            (operativo + degradado)
            <br />/ (total − bloqueado − sin datos)
          </div>
          <div>
            <span className="text-panel-muted">nueves =</span> floor(−log10(1 − uptime))
          </div>
          <div className="text-[13px] text-panel-muted">
            99,41 % → −log10(0,0059) = 2,23 → 2 nueves
          </div>
        </div>
      </section>

      <section aria-labelledby="catalogo" className="flex flex-col gap-4">
        <h2 id="catalogo" className="m-0 font-display text-[24px] font-bold">
          Qué servicios y cada cuánto
        </h2>
        {catalog.isError ? (
          <p role="alert" className="m-0 text-[15px] text-muted">
            No pudimos leer el catálogo. Reinténtalo más tarde.
          </p>
        ) : !isConfigured || (catalog.data?.length ?? 0) === 0 ? (
          <p className="m-0 text-[15px] text-muted">Catálogo sin datos.</p>
        ) : (
          <ProbeCatalog probes={catalog.data ?? []} />
        )}
      </section>

      <section className="flex flex-wrap gap-6">
        <div className="flex min-w-[280px] flex-[1_1_400px] flex-col gap-2.5 rounded-2xl border border-line bg-surface p-6">
          <h2 className="m-0 font-display text-[20px] font-bold">Juego limpio</h2>
          <ul className="m-0 list-disc pl-5 text-[15px] leading-relaxed text-ink-soft">
            <li>
              La sonda se presenta como <span className="font-mono text-[13px]">anden9-probe</span>,
              no se hace pasar por un navegador.
            </li>
            <li>Nunca intenta saltarse una cola, un captcha o un bloqueo.</li>
            <li>Una petición a la vez por servicio y un máximo de 150 peticiones por hora.</li>
            <li>No guarda claves ni tokens de Renfe, solo si se pudieron obtener.</li>
          </ul>
        </div>
        <div className="flex min-w-[280px] flex-[1_1_400px] flex-col gap-2.5 rounded-2xl border border-line bg-surface p-6">
          <h2 className="m-0 font-display text-[20px] font-bold">Lo que no vemos</h2>
          <ul className="m-0 list-disc pl-5 text-[15px] leading-relaxed text-ink-soft">
            <li>Medimos desde [REGIÓN DE LA SONDA]. Un fallo regional puede no verse aquí, o verse solo aquí.</li>
            <li>Vemos la puerta, no la cocina: nada de los sistemas internos de Renfe.</li>
            <li>La venta clásica se retira cuando la nueva venda todos los viajes (25 ene 2027).</li>
          </ul>
        </div>
      </section>

      <p className="m-0 text-[14px] leading-relaxed text-muted">
        Los endpoints salen de{' '}
        <a
          href="https://github.com/luisgonzaleznf/renfe-cli"
          target="_blank"
          rel="noreferrer"
          className="text-link underline hover:text-ink"
        >
          renfe-cli
        </a>
        , de Luis González, con licencia MIT. Nueves es un proyecto independiente: no está afiliado,
        respaldado ni soportado por Renfe.
      </p>
    </main>
  )
}

const STATES = [
  {
    name: 'Operativo',
    dot: 'bg-up',
    text: 'Responde con el código esperado, la forma de datos correcta y por debajo del umbral de latencia.',
    count: 'Cuenta como disponible',
    badge: 'bg-up-surface text-up-ink',
  },
  {
    name: 'Degradado',
    dot: 'bg-degraded',
    text: 'Responde bien pero lento, o con datos viejos. Se ve en la página y en el detalle.',
    count: 'Cuenta como disponible',
    badge: 'bg-up-surface text-up-ink',
  },
  {
    name: 'Caído',
    dot: 'bg-down',
    text: 'Timeout, conexión rechazada, 5xx o una respuesta que no tiene la forma esperada (un 200 con HTML de error también).',
    count: 'Cuenta en contra',
    badge: 'bg-down-surface text-down-ink',
  },
  {
    name: 'Bloqueado',
    dot: 'bg-blocked-stripes',
    text: '403, 429, una página de protección o una sala de espera. Renfe ha decidido no hablar con la sonda.',
    count: 'No cuenta',
    badge: 'bg-neutral-surface text-ink-soft',
  },
  {
    name: 'Sin datos',
    dot: 'bg-nodata',
    text: 'La sonda no llegó a medir, o el endpoint de control tampoco respondía: el problema era nuestro.',
    count: 'No cuenta',
    badge: 'bg-neutral-surface text-ink-soft',
  },
]
