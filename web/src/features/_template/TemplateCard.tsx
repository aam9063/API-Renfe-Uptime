import type { ReactNode } from 'react'

type TemplateCardProps = {
  title: string
  children: ReactNode
}

export function TemplateCard({ title, children }: TemplateCardProps) {
  return (
    <section className="rounded-2xl border border-line bg-surface p-6">
      <h2 className="font-display text-lg font-bold">{title}</h2>
      <div className="mt-3 text-[15px] leading-relaxed text-ink-soft">{children}</div>
    </section>
  )
}
