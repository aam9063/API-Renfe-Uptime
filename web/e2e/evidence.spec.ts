import { expect, test } from '@playwright/test'

test('evidence capture of the shell', async ({ page }, testInfo) => {
  await page.goto('/')
  await expect(page.getByText('No oficial · sin relación con Renfe')).toBeVisible()

  await page.screenshot({
    path: `.evidence/${testInfo.project.name}/shell.png`,
    fullPage: true,
  })
})
