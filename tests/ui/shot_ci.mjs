// Screenshot capture for CI/site evidence (docs/screenshots/ 05-09).
// Usage (workdir tests/ui):
//   node shot_ci.mjs <deploy-artifact-dir>
// Captures: 05 actions page, 06 pytest-html, 07 playwright report,
// 08 live failure gallery, 09 live site home.
import { chromium } from "playwright";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(here, "..", "..");
const OUT = path.join(ROOT, "docs", "screenshots");
const ART = process.argv[2];
if (!ART) throw new Error("usage: shot_ci.mjs <deploy-artifact-dir>");

fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const shot = async (url, file, opts = {}) => {
  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(600);
  const p = path.join(OUT, file);
  await page.screenshot({ path: p, ...opts });
  console.log(file, fs.statSync(p).size, "bytes");
};

const toFileUrl = (p) => "file:///" + path.resolve(p).replace(/\\/g, "/");

// 05 — Actions overview (public)
await shot("https://github.com/AKARandy/QUACKO/actions", "05-actions-green.png");

// 06 — pytest-html from the green deploy artifact
await shot(toFileUrl(path.join(ART, "report", "api-model.html")), "06-pytest-report.png");

// 07 — Playwright HTML report from the green deploy artifact
await shot(
  toFileUrl(path.join(ART, "tests", "ui", "playwright-report", "index.html")),
  "07-playwright-report.png"
);

// 08 — live failure gallery (green run -> explicit no-failures state)
await shot("https://akarandy.github.io/QUACKO/failure-gallery/", "08-failure-gallery.png");

// 09 — live site home (viewport: fullPage exceeds the 300 KB evidence budget)
await shot("https://akarandy.github.io/QUACKO/", "09-github-io-site.png");

await browser.close();
console.log("OK: screenshots ->", OUT);
