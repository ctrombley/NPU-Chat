import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:1314',
    headless: true,
  },
  webServer: {
    command: 'cd .. && python3 npuchat.py',
    port: 1314,
    reuseExistingServer: true,
    timeout: 15000,
  },
});
