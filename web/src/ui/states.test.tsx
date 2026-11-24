import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ErrorState, LoadingState, NoDataState } from './states'

describe('the shared states', () => {
  it('announces the loading state', () => {
    render(<LoadingState />)
    expect(screen.getByRole('status').textContent).toContain('Cargando…')
  })

  it('explains why there are no data, for real', () => {
    render(<NoDataState />)
    expect(screen.getByRole('status').textContent).toContain('Sin datos')
    expect(screen.getByRole('status').textContent).toContain('no puede alcanzar la base de datos')
  })

  it('accepts a custom label for the empty state', () => {
    render(<NoDataState label="Servicio no encontrado" />)
    expect(screen.getByText('Servicio no encontrado')).toBeDefined()
  })

  it('offers a retry that is a real button', () => {
    const onRetry = vi.fn()
    render(<ErrorState onRetry={onRetry} />)
    expect(screen.getByRole('alert').textContent).toContain('No pudimos cargar los datos')
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
