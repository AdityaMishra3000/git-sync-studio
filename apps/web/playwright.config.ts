import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests run against a *running stack*, not against mocks.
 *
 *   docker compose up -d          # web + api + postgres + redis + worker
 *   npm run test:e2e:install      # once, downloads the browser
 *   E2E_BASE_URL=http://localhost:3100 npm run test:e2e
 *
 * With no E2E_BASE_URL, Playwright starts `next dev` itself and expects the API
 * to already be reachable at NEXT_PUBLIC_API_BASE_URL.
 */
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:3100";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: "npm run dev -- --port 3100",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
