import { defineConfig, devices } from "@playwright/test"

const baseURL = "http://127.0.0.1:3000"

export default defineConfig({
  testDir: "./tests/e2e",
  outputDir: ".next/playwright-results",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run build && npm run start",
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    env: {
      NEXTAUTH_SECRET: "e2e-nextauth-secret",
      INTERNAL_JWT_SECRET: "e2e-internal-jwt-secret",
      INTERNAL_RESOLVE_SECRET: "e2e-internal-resolve-secret",
      GOOGLE_CLIENT_ID: "e2e-google-client-id",
      GOOGLE_CLIENT_SECRET: "e2e-google-client-secret",
      NEXTAUTH_URL: baseURL,
      BACKEND_URL: "http://127.0.0.1:8000",
      NEXT_TELEMETRY_DISABLED: "1",
    },
  },
})
