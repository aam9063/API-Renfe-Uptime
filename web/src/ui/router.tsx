import { type MouseEventHandler, type ReactNode, useSyncExternalStore } from 'react'

// A tiny history-based router. The three routes of M4 do not justify a router
// dependency: pushState, a snapshot string and useSyncExternalStore are enough.

const NAVIGATE_EVENT = 'anden9:navigate'

export type RouteLocation = {
  path: string
  hash: string
}

function snapshot(): string {
  return `${window.location.pathname}${window.location.hash}`
}

function subscribe(callback: () => void): () => void {
  window.addEventListener('popstate', callback)
  window.addEventListener(NAVIGATE_EVENT, callback)
  return () => {
    window.removeEventListener('popstate', callback)
    window.removeEventListener(NAVIGATE_EVENT, callback)
  }
}

export function useRouteLocation(): RouteLocation {
  const location = useSyncExternalStore(subscribe, snapshot)
  const hashStart = location.indexOf('#')
  if (hashStart < 0) {
    return { path: location, hash: '' }
  }
  return { path: location.slice(0, hashStart), hash: location.slice(hashStart) }
}

export function navigate(to: string): void {
  window.history.pushState({}, '', to)
  window.dispatchEvent(new Event(NAVIGATE_EVENT))
  const hashStart = to.indexOf('#')
  if (hashStart >= 0) {
    document.getElementById(to.slice(hashStart + 1))?.scrollIntoView({ block: 'start' })
  } else {
    window.scrollTo({ top: 0 })
  }
}

export type LinkProps = {
  to: string
  children: ReactNode
  className?: string
  ariaLabel?: string
  onNavigate?: () => void
}

export function Link({ to, children, className, ariaLabel, onNavigate }: LinkProps) {
  const handleClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
    event.preventDefault()
    navigate(to)
    onNavigate?.()
  }
  return (
    <a href={to} className={className} aria-label={ariaLabel} onClick={handleClick}>
      {children}
    </a>
  )
}
