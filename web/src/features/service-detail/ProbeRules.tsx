import { formatInterval } from '../../lib/format'
import type { ProbeRow } from '../../data/hooks'

// The rules the probe follows, from the methodology of the design. The
// interval and timeout lines are catalog data; the outcome rules are the
// same for every probe.

export function ProbeRules({ probe }: { probe: ProbeRow | null }) {
  const intervalLine =
    probe === null
      ? null
      : `Cada ${formatInterval(probe.interval_s)}, timeout de ${formatInterval(probe.timeout_s)}.`

  return (
    <div className="flex flex-col gap-3.5 rounded-2xl bg-panel p-6 text-surface">
      <h2 className="m-0 font-display text-[20px] font-bold">Qué comprueba la sonda</h2>
      {intervalLine !== null && (
        <div className="flex flex-col gap-1 border-b border-panel-line pb-3">
          <span className="text-[12px] uppercase tracking-[0.06em] text-panel-muted">
            Intervalo y timeout
          </span>
          <span className="text-[14px] leading-relaxed">{intervalLine}</span>
        </div>
      )}
      {RULES.map((rule) => (
        <div key={rule.title} className="flex flex-col gap-1 border-b border-panel-line pb-3">
          <span className="text-[12px] uppercase tracking-[0.06em] text-panel-muted">
            {rule.title}
          </span>
          <span className="text-[14px] leading-relaxed">{rule.text}</span>
        </div>
      ))}
    </div>
  )
}

const RULES = [
  {
    title: 'Operativo',
    text: 'Responde con el código esperado, la forma de datos correcta y por debajo del umbral de latencia.',
  },
  {
    title: 'Degradado',
    text: 'Responde bien pero lento, o con datos viejos. Se ve en la página y en el detalle.',
  },
  {
    title: 'Caído',
    text: 'Timeout, conexión rechazada, 5xx o una respuesta que no tiene la forma esperada. Se confirma con 2 fallos seguidos.',
  },
  {
    title: 'Bloqueado',
    text: '403, 429 o una página de protección. Se muestra, pero no cuenta para el uptime.',
  },
  {
    title: 'Sin datos',
    text: 'La propia sonda falla o el endpoint de control tampoco responde. Tampoco cuenta.',
  },
]
