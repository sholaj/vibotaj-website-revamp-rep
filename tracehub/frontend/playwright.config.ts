import { defineConfig, devices } from '@playwright/test';

/**
 * TraceHub E2E Test Configuration
 * 
 * Playwright configuration for testing all 6 user roles and their journeys:
 * ADMIN, COMPLIANCE, LOGISTICS_AGENT, BUYER, SUPPLIER, VIEWER
 * 
 * Run tests:
 *   npm run e2e               # Run all tests
 *   npm run e2e:ui            # Interactive UI mode
 *   npm run e2e:headed        # See browser while running
 *   npm run e2e:debug         # Pause and debug
 */

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Run tests sequentially to avoid data conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 1, // Single worker for data consistency
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:80',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment to test on other browsers
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // No webServer configuration - Docker Compose should already be running
  // Start Docker Compose manually before running tests:
  //   cd tracehub && docker-compose up -d

  timeout: 30 * 1000,
  expect: {
    timeout: 5 * 1000,
  },

  globalTimeout: 30 * 60 * 1000, // 30 minutes total
});
