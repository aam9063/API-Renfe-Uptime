import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { App } from './App'

const NAVIGATE_EVENT = 'anden9:navigate'

function renderAt(path: string) {
  act(() => {
    window.history.pushState({}, '', path)
    window.dispatchEvent(new Event(NAVIGATE_EVENT))
  })
  render(<App />)
}

afterEach(() => {
  act(() => {
    window.history.pushState({}, '', '/')
    window.dispatchEvent(new Event(NAVIGATE_EVENT))
  })
})

describe('the shell and the routes', () => {
  it('shows the unofficial notice on every route', () => {
    render(<App />)
    for (const path of ['/', '/metodologia', '/servicio/live-map', '/algun-sitio-inexistente']) {
      act(() => {
        window.history.pushState({}, '', path)
        window.dispatchEvent(new Event(NAVIGATE_EVENT))
      })
      expect(screen.getAllByText('No oficial · sin relación con Renfe').length, path).toBeGreaterThan(0)
    }
  })

  it('understands the three routes', () => {
    renderAt('/')
    expect(screen.getByRole('heading', { name: '¿Cuántos nueves tiene Renfe?' })).toBeDefined()

    act(() => {
      window.history.pushState({}, '', '/metodologia')
      window.dispatchEvent(new Event(NAVIGATE_EVENT))
    })
    expect(screen.getByRole('heading', { name: 'Cómo medimos' })).toBeDefined()

    act(() => {
      window.history.pushState({}, '', '/servicio/live-map')
      window.dispatchEvent(new Event(NAVIGATE_EVENT))
    })
    expect(screen.getByRole('heading', { name: 'Detalle del servicio' })).toBeDefined()
  })

  it('has a page not found for unknown paths', () => {
    renderAt('/calleja-sin-salida')
    expect(
      screen.getByRole('heading', { name: 'Página no encontrada' }),
    ).toBeDefined()
  })

  it('changes the document title per route', () => {
    renderAt('/metodologia')
    expect(document.title).toBe('Nueves, metodología')
  })
})
