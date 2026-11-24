import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

// Accessibility is part of the definition of done: no serious or critical
// axe violation on any route, on either viewport.

const ROUTES = ['/', '/metodologia', '/servicio/live-map']

async function scanAccessibility(page: Page, path: string): Promise<string[]> {
  await page.goto(path)
  const results = await new AxeBuilder({ page }).analyze()
  return results.violations
    .filter((violation) => violation.impact === 'serious' || violation.impact === 'critical')
    .map((violation) => `${violation.id}: ${violation.nodes.length} node(s)`)
}

for (const path of ROUTES) {
  test(`axe finds no serious or critical violation on ${path}`, async ({ page }) => {
    const violations = await scanAccessibility(page, path)
    expect(violations).toEqual([])
  })
}
