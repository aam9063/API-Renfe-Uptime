import { type ReactNode, useState } from 'react'

import { OfficialNotice } from './OfficialNotice'
import { Link, useRouteLocation } from './router'

const REPO_URL = 'https://github.com/aam9063/API-Renfe-Uptime'

const NAV_ITEMS = [
  { to: '/', label: 'Estado' },
  { to: '/#incidentes', label: 'Incidentes' },
  { to: '/metodologia', label: 'Metodología' },
]

function isActiveRoute(currentPath: string, to: string): boolean {
  if (to === '/') {
    return currentPath === '/'
  }
  return currentPath === to
}

export function Shell({ children }: { children: ReactNode }) {
  const { path } = useRouteLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="flex min-h-screen flex-col bg-canvas text-ink">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-x-8 gap-y-4 px-5 py-3.5 md:px-8 md:py-4">
          <Link
            to="/"
            onNavigate={closeMenu}
            className="flex items-center gap-2.5 text-ink no-underline hover:text-ink"
          >
            <span className="flex h-[30px] w-[30px] items-center justify-center rounded-[7px] bg-panel font-mono text-[14px] font-semibold text-surface md:h-[34px] md:w-[34px] md:rounded-lg md:text-[16px]">
              A9
            </span>
            <span className="font-display text-[20px] font-bold md:text-[22px]">Andén 9</span>
          </Link>
          <nav
            aria-label="Principal"
            className="hidden flex-1 flex-wrap items-center gap-6 text-[15px] font-medium md:flex"
          >
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={
                  isActiveRoute(path, item.to) ? 'text-ink' : 'text-muted hover:text-ink'
                }
              >
                {item.label}
              </Link>
            ))}
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="text-muted hover:text-ink"
            >
              Código
            </a>
          </nav>
          <div className="hidden md:block">
            <OfficialNotice />
          </div>
          <button
            type="button"
            aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
            aria-expanded={menuOpen}
            aria-controls="menu-movil"
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex h-11 w-11 items-center justify-center rounded-[10px] border border-line bg-surface text-ink md:hidden"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>
        </div>
        {menuOpen && (
          <nav
            id="menu-movil"
            aria-label="Principal"
            className="flex flex-col items-start gap-4 border-t border-line bg-surface px-5 py-4 text-[15px] font-medium md:hidden"
          >
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onNavigate={closeMenu}
                className={
                  isActiveRoute(path, item.to) ? 'text-ink' : 'text-muted hover:text-ink'
                }
              >
                {item.label}
              </Link>
            ))}
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="text-muted hover:text-ink"
            >
              Código
            </a>
          </nav>
        )}
      </header>

      <div className="px-5 pt-5 md:hidden">
        <OfficialNotice />
      </div>

      <main className="mx-auto flex w-full max-w-[1200px] flex-1 flex-col gap-5 px-5 py-5 md:gap-10 md:px-8 md:py-10">
        {children}
      </main>

      <footer className="border-t border-line bg-surface">
        <div className="mx-auto flex max-w-[1200px] flex-wrap gap-x-8 gap-y-3 px-5 py-6 text-[13px] leading-relaxed text-muted md:px-8">
          <p className="m-0 min-w-[280px] flex-[2_1_480px]">
            Proyecto independiente y no oficial. No está afiliado, respaldado ni soportado por
            Renfe. Medimos desde fuera, con una sonda que se identifica con su propio user agent y
            nunca intenta saltarse colas, captchas ni bloqueos.
          </p>
          <p className="m-0 min-w-[240px] flex-[1_1_280px]">
            Sondas desde [REGIÓN DE LA SONDA] · cada 1 a 15 min · endpoints tomados de{' '}
            <a
              href="https://github.com/luisgonzaleznf/renfe-cli"
              target="_blank"
              rel="noreferrer"
              className="text-link underline hover:text-ink"
            >
              renfe-cli
            </a>{' '}
            (MIT)
          </p>
        </div>
      </footer>
    </div>
  )
}
