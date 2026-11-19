import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/browser",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3000",
    launchOptions: { channel: process.env.AILEO_BROWSER_CHANNEL || undefined },
  },
  webServer: [
    { command: "uv run --locked uvicorn aileo.main:app --app-dir services/api --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/readyz", reuseExistingServer: !process.env.CI },
    { command: "pnpm --filter @aileo/web start --hostname 127.0.0.1",
      url: "http://127.0.0.1:3000", reuseExistingServer: !process.env.CI },
  ],
});
