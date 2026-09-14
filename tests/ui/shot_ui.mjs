// Screenshot capture for the evidence site (docs/screenshots/).
// Usage (workdir tests/ui, SUT on :5000 for "ui" mode):
//   node shot_ui.mjs ui
//   node shot_ui.mjs gallery file:///abs/path/site/failure-gallery/index.html
import { chromium } from "playwright";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(here, "..", "..");
const OUT = path.join(ROOT, "docs", "screenshots");
const BASE = "http://127.0.0.1:5000/";
const mode = process.argv[2];

fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

if (mode === "gallery") {
  const url = process.argv[3];
  if (!url) throw new Error("usage: shot_ui.mjs gallery <file-url>");
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT, "11-gallery-proof.png") });
} else if (mode === "ui") {
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () => !document.getElementById("chart-svg").hidden,
    null,
    { timeout: 15000 }
  ).catch(() => {});
  await page.waitForTimeout(300);

  // 01 — fresh dashboard, empty upload state
  await page.screenshot({ path: path.join(OUT, "01-upload-empty.png"), fullPage: true });

  // 02 — real receipt through the real engine (hero)
  const receipt = path.join(ROOT, "data", "golden", "img_0000.jpg");
  await page.setInputFiles("#file-input", receipt);
  await page.waitForFunction(
    () => document.getElementById("res-text").textContent.trim().length > 0,
    null,
    { timeout: 90000 }
  );
  await page.waitForFunction(
    () => !document.getElementById("pv-canvas").hidden,
    null,
    { timeout: 90000 }
  );
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT, "02-result-valid.png"), fullPage: true });

  // 03 — non-image upload shows the real API error
  await page.click("#clear-btn");
  await page.waitForSelector("#dropzone:not([hidden])");
  const tmpTxt = path.join(ROOT, "report", "shot-negative.txt");
  fs.mkdirSync(path.dirname(tmpTxt), { recursive: true });
  fs.writeFileSync(tmpTxt, "this is not an image\n");
  await page.setInputFiles("#file-input", tmpTxt);
  await page.waitForFunction(
    () => !document.getElementById("error").hidden,
    null,
    { timeout: 30000 }
  );
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, "03-error-invalid.png"), fullPage: true });

  // 04 — clear returns to the empty state (clear lives in the result state,
  // so recover via a valid upload first — matches the committed UI-3 flow)
  await page.setInputFiles("#file-input", receipt);
  await page.waitForFunction(
    () => document.getElementById("res-text").textContent.trim().length > 0,
    null,
    { timeout: 90000 }
  );
  await page.click("#clear-btn");
  await page.waitForSelector("#dropzone:not([hidden])");
  await page.waitForFunction(
    () => document.getElementById("res-text").textContent.trim().length === 0,
    null,
    { timeout: 5000 }
  );
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, "04-clear-reset.png"), fullPage: true });
} else {
  throw new Error("usage: shot_ui.mjs ui | gallery <file-url>");
}

await browser.close();
console.log("OK: screenshots ->", OUT);
