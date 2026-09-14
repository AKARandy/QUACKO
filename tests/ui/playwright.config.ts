import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./specs",
  timeout: 120000,
  retries: 0,
  reporter: [
    ["html", { open: "never" }],
    ["junit", { outputFile: "../../report/junit-ui.xml" }],
    ["list"],
  ],
  use: {
    baseURL: process.env.QUACKO_BASE || "http://127.0.0.1:5000",
    headless: true,
    viewport: { width: 1280, height: 800 },
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
