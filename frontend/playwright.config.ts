import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'cd ../backend && uv run uvicorn backend.app:app --host 127.0.0.1 --port 8000',
      port: 8000,
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: 'bun run dev --host 127.0.0.1 --port 4173',
      port: 4173,
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
})
