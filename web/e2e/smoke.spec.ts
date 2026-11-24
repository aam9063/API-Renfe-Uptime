import { expect, test } from '@playwright/test'

const NOTICE = 'No oficial · sin relación con Renfe'

test('the shell loads with the unofficial notice and no console error', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  await page.goto('/')

  // The header chip and the mobile strip are two pieces of the same notice:
  // exactly one of them is visible on each viewport.
  const notices = page.getByText(NOTICE)
  await expect(notices).toHaveCount(2)

  await expect(notices.filter({ visible: true }).first()).toBeVisible()
  expect(consoleErrors).toEqual([])
})
