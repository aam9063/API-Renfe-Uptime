import { expect, test } from '@playwright/test'

// The four routes of the site, walked in both viewports. Without database
// variables the app renders its "sin datos" state instead of crashing, which
// is exactly what this run asserts; with a local database up, the same walk
// changes the window tab and follows a service into its detail page.

const NOTICE = 'No oficial · sin relación con Renfe'
const ROUTES = ['/', '/metodologia', '/servicio/live-map', '/calleja-sin-salida']
const DB_CONFIGURED = Boolean(
  process.env.VITE_SUPABASE_URL && process.env.VITE_SUPABASE_ANON_KEY,
)

test('the unofficial notice is on every route, with no console error', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  for (const path of ROUTES) {
    await page.goto(path)
    await expect(page.getByText(NOTICE).filter({ visible: true }).first(), path).toBeVisible()
  }
  expect(consoleErrors, ROUTES.join(', ')).toEqual([])
})

test('walks the home, the window change, the detail of a service and the methodology', async ({
  page,
}) => {
  await page.goto('/')

  if (DB_CONFIGURED) {
    await expect(page.getByRole('heading', { name: '¿Cuántos nueves tiene Renfe?' })).toBeVisible()
    await page.getByRole('tab', { name: '90d' }).click()
    await expect(page.getByRole('tab', { name: '90d' })).toHaveAttribute('aria-selected', 'true')
    await page.getByRole('link', { name: /^Mapa en vivo/ }).first().click()
    await expect(page.getByRole('heading', { name: 'Últimos 90 días' })).toBeVisible()
  } else {
    await expect(page.getByText('Sin datos').first()).toBeVisible()
  }

  await page.goto('/metodologia')
  await expect(page.getByRole('heading', { name: 'Cómo medimos' })).toBeVisible()
  await expect(page.getByText('uptime =')).toBeVisible()
})
