import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TemplateCard } from '.'

describe('TemplateCard', () => {
  it('renders its title and content', () => {
    render(<TemplateCard title="Servicios">Contenido</TemplateCard>)

    expect(screen.getByRole('heading', { name: 'Servicios' })).toBeDefined()
    expect(screen.getByText('Contenido')).toBeDefined()
  })
})
