import { expect, test } from '@playwright/test'

test('the shell loads with the unofficial notice and no console error', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  await page.goto('/')

  await expect(page.getByText('No oficial · sin relación con Renfe')).toBeVisible()
  expect(consoleErrors).toEqual([])
})
