import { expect, test } from '@playwright/test'

const NOTICE = 'No oficial · sin relación con Renfe'
const DB_CONFIGURED = Boolean(
  process.env.VITE_SUPABASE_URL && process.env.VITE_SUPABASE_ANON_KEY,
)

test('evidence captures of the three screens', async ({ page }, testInfo) => {
  await page.goto('/')
  await expect(page.getByText(NOTICE).filter({ visible: true }).first()).toBeVisible()
  await page.screenshot({
    path: `.evidence/${testInfo.project.name}/home.png`,
    fullPage: true,
  })

  if (DB_CONFIGURED) {
    await page.getByRole('link', { name: /^Mapa en vivo/ }).first().click()
  } else {
    await page.goto('/servicio/live-map')
    await expect(page.getByText('Sin datos').first()).toBeVisible()
  }
  await page.screenshot({
    path: `.evidence/${testInfo.project.name}/service.png`,
    fullPage: true,
  })

  await page.goto('/metodologia')
  await expect(page.getByRole('heading', { name: 'Cómo medimos' })).toBeVisible()
  await page.screenshot({
    path: `.evidence/${testInfo.project.name}/methodology.png`,
    fullPage: true,
  })
})
