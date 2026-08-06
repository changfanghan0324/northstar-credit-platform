import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 45_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], browserName: "chromium" },
    },
  ],
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : [
        {
          command:
            "cd ../.. && PYTHONPATH=packages/credit_engine:packages/credit_app:packages/policy:apps/api .venv-rebuilt/bin/python -m uvicorn northstar_api.main:app --host 127.0.0.1 --port 8000",
          url: "http://127.0.0.1:8000/health",
          reuseExistingServer: true,
          timeout: 60_000,
        },
        {
          command:
            "NORTHSTAR_API_PROXY_TARGET=http://127.0.0.1:8000 next dev --hostname 127.0.0.1 --port 3000",
          url: "http://localhost:3000",
          reuseExistingServer: true,
          timeout: 60_000,
        },
      ],
});
