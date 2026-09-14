import { test, expect } from "@playwright/test";
import * as path from "path";

const GOLDEN = path.join(__dirname, "..", "..", "..", "data", "golden", "img_0000.jpg");
const BAD = path.join(__dirname, "..", "..", "fixtures", "not-an-image.txt");

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("UI-1 valid upload shows extracted text", async ({ page }) => {
  await page.locator("#file-input").setInputFiles(GOLDEN);
  await expect(page.locator("#res-text")).not.toBeEmpty();
  await expect(page.locator("#pv-canvas")).toBeVisible();
});

test("UI-2 invalid file shows error", async ({ page }) => {
  await page.locator("#file-input").setInputFiles(BAD);
  await expect(page.locator("#error")).toBeVisible();
});

test("UI-3 clear resets form", async ({ page }) => {
  await page.locator("#file-input").setInputFiles(GOLDEN);
  await expect(page.locator("#res-text")).not.toBeEmpty();
  await page.locator("#clear-btn").click();
  await expect(page.locator("#res-text")).toBeEmpty();
  await expect(page.locator("#dropzone")).toBeVisible();
  expect(await page.locator("#file-input").inputValue()).toBe("");
});
