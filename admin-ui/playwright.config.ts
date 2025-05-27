import { defineConfig, devices } from '@playwright/test';

// Read PLAYWRIGHT_BASE_URL from environment, default to Vite dev server URL
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

export default defineConfig({
  testDir: './src/e2e', // Directory for E2E tests
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html', // HTML reporter for viewing results
  
  use: {
    baseURL: baseURL, // Use the environment variable or default
    trace: 'on-first-retry', // Collect trace on first retry
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Configure a web server if not testing a deployed URL.
  // If PLAYWRIGHT_BASE_URL is set, it implies we are testing a live/deployed environment,
  // so we should not start the local dev server.
  webServer: process.env.PLAYWRIGHT_BASE_URL 
    ? undefined // Do not start a web server if PLAYWRIGHT_BASE_URL is set
    : {
        command: 'pnpm run dev', // Command to start dev server
        url: 'http://localhost:5173', // Must match the default baseURL
        reuseExistingServer: !process.env.CI, // In CI, always start a new server
        timeout: 120 * 1000, // Increase timeout for server start
        // Example of how to handle stdout/stderr if needed for debugging
        // stdout: 'pipe', 
        // stderr: 'pipe',
      },
});
