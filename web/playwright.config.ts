import { defineConfig, devices } from '@playwright/test'

const PREVIEW_URL = 'http://127.0.0.1:4319'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: PREVIEW_URL,
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'pnpm build && pnpm preview --port 4319 --strictPort --host 127.0.0.1',
    url: PREVIEW_URL,
    reuseExistingServer: true,
    timeout: 180_000,
  },
  projects: [
    {
      name: 'desktop',
      testIgnore: /evidence/,
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'mobile',
      testIgnore: /evidence/,
      use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 } },
    },
    {
      name: 'evidence',
      testMatch: /evidence/,
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
  ],
})
