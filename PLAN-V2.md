# QUACKO PLAN V2 — Tesseract Edition (Committed-20, 3 Layers, 2 Workflows)

**Status: IMPLEMENTED locally 2026-09-14 (all hard gates green — see ADDENDUM + `docs/quality-gates.md`); GitHub repo/CI/Pages = PLANNED (Phase 4).**
**Supersedes:** `PLAN.md` (RapidOCR/full-973/7-workflow plan) where they conflict, per user order 2026-09-14 ("definitive blueprint").
**Survives:** the NO-LARP honesty layer (`PLAN.md` §8 / `AGENTS.md`) — it binds this plan unchanged.

Principles (user): **zero wasted compute, zero hallucinated dependencies, maximum demonstrable QA depth.**

## 0. What changed vs PLAN.md (supersession record)

| Item | PLAN.md (dead) | PLAN-V2 (this file) |
|---|---|---|
| OCR engine | rapidocr_onnxruntime 1.4.4 (PP-OCRv4) | **pytesseract + Tesseract 5.x** |
| Data | FULL 973 images, CI-fetched, gitignored | **20 real SROIE images COMMITTED** to `data/golden/` (~5–10 MB, EST.) |
| Degradation | `data/generated/` on disk | **in-memory only** (cv2/Pillow in fixture setup) |
| Response shape | `{text, confidence[], boxes[]}` (array) | **`{text, confidence: float, boxes: [[x,y,w,h]]}`** (LOCKED, new) |
| Test layers | UI×2 + API×2 + JMeter + model | **API+Model (pytest) + UI (Playwright, 3 tests)** |
| Workflows | 7 (blocking chain) | **2**: `ci.yml` (PR, blocking) + `deploy.yml` (main, Pages) |
| Dropped suites | — | Selenium, RestAssured, Postman/Newman, JMeter (no enterprise bloat) |
| Nuke lock (§6.4/NUKE.md) | locked delete commands | **Moot** — repo is ~10 MB; nothing heavy exists to delete |
| Evidence | gh-pages multi-report | **mkdocs-material site** + embedded pytest-html + Playwright HTML + **failure gallery** + **screenshot batch (§5.1)** |
| Repo/CI/deploy ownership | "assistant creates repo LATER" | **This agent does the full chain**: repo creation → commits → CI/CD → GitHub Pages (user order 2026-09-14) |
| SUT UI | "minimal form" | **Mimics/copy `THIS_UI_EXAMPLE.jpg`** (user order 2026-09-14, §3.5) |

Deliberate scope note: the existing local scaffold (`selenium-tests/`, `restassured-tests/`,
`postman/`, `jmeter/`, `src/`, `tests/`, `app.py`, `mvnw*`, `.mvn/`) is **not ported**.
It stays on disk untouched (no delete orders in this plan); the new repo is built in the
layout of §6. Historical records (`PLAN.md`, `AGENTS.md`, `NUKE.md`,
`WHYMUSESPARKISRETARDED.md`) move to `docs/history/` — evidence, not dead weight.
DECIDED 2026-09-14 (user): they live in `docs/history/`, **gitignored** (kept on disk,
never in the repo); `AGENTS.md` is synced in place to V2 rules (old copy kept as
`docs/history/AGENTS-V1.md`).

## ADDENDUM 2026-09-14 — Spec re-derivation (Option C), user order

Supersedes the §3.2/§3.3 acceptance-CER gate text: the 0.05 / 0.25 / ≤0.05 / strict /
+0.01 assertions were **blueprint placeholders, not product requirements** — Tesseract 5
is a general-purpose engine, and 95% field accuracy on photo receipts was never a
credible promise (first full measurement: clean mean 0.086, worst 0.222). The live spec
is now `docs/quality-gates.md` (standard ML-QA split: **accuracy = telemetry, stability
= gates**):

1. **Hard gates (pass/fail, block CI):** API contract (API-1..5,7; API-6 latency
   demoted to telemetry), invariants I1–I3, metamorphic relations — M1 rotation
   stability ≤ 0.20 (measured worst 0.1454), M2 **strict aggregate** noise
   monotonicity Σheavy ≥ Σlight (measured 11.2355 ≥ 6.389), M3 scale stability
   ≤ +0.10 (measured worst +0.0583) — UI-1..3 (deploy tier).
2. **Accuracy telemetry (no pass/fail):** absolute field-CER (clean, blur, all
   variants) measured every run → `data/baselines/metrics.json` (`last_run`) →
   dashboard. A telemetry test failing = broken measurement pipeline, not an
   accuracy statement.
3. **Regression gate (pass/fail):** per-receipt clean & blur CER ≤
   max(0.01, 1.10 × committed baseline). Baseline provenance (OS + Tesseract
   version + pipeline) is recorded in `metrics.json`; a red with provenance
   mismatch and no code change = environment delta → re-baseline from CI
   artifacts under a logged order (environment correction, procedure in
   `docs/quality-gates.md`).

Measured 2026-09-14, local Windows-11 / Tesseract 5.5.0.20241111 / Python 3.12.6,
pipeline `gray+normalize(1600-2400)+gated-deskew+psm6`: API 7/7, invariants 3/3,
metamorphic 3/3, regression 2/2, UI 3/3 — **all hard gates green (VERIFIED, this
session)**. CI (ubuntu + apt Tesseract) is a different provenance; first CI run may
trigger the documented re-baseline procedure.

## 1. Facts verified on this machine (2026-09-14, this session)

- Tesseract installed: `C:\Program Files\Tesseract-OCR\tesseract.exe`, **v5.5.0.20241111** (leptonica 1.85.0). On PATH (`where.exe tesseract` found it) → `pytesseract` works locally with no `tesseract_cmd` hack.
- Python **3.12.6** (`C:\Python312`), pip 26.2.1.
- `data/golden/labels.jsonl` = **973 lines**, shape `{"file": "img_NNNN.jpg", "text": "<4 lines>"}` — GT is **4 key fields per receipt** (merchant name, date, address, total), NOT full-page transcription. This drives the CER definition in §3.2 (the exact trap that broke the old CER gates, `quality-gates.md:7-16`).
- `data/golden/MANIFEST.sha256` = 973 pinned hashes, `<sha256>  img_NNNN.jpg` format.
- Source dataset: `podbilabs/sroie-donut` (HF), image numbering = sorted walk order (see old `scripts/download_data.py:55-60`); the 20 pins in §2 were selected from the existing verified labels + manifest.
- 317 distinct merchant stores across the 973 → the 20 below are 20 different stores, evenly spread across the set.
- GitHub identity (VERIFIED via `gh auth status`): account **AKARandy** (scopes `repo`, `workflow`, `user`, `gist`, `read:org`) → this agent can create the repo, push, and trigger Actions. Repo will be `https://github.com/AKARandy/QUACKO`, site `https://AKARandy.github.io/QUACKO/` (PLANNED until Phase 4 creates them).
- UI reference (user order 2026-09-14): `THIS_UI_EXAMPLE.jpg` at repo root — **1200×1200 RGB** (VERIFIED) — is the design the SUT `GET /` page must mimic/copy. It will be committed to `docs/ui-reference/` as the visual spec (§3.5).

## 2. Data: "The Committed 20" (pinned now, not at build time)

**Rule:** 20 diverse real SROIE Task-1 receipts, committed to `data/golden/`, SHA256-pinned.
No synthetic data, no runtime download for tests, no silent subsetting — the subset is
explicit, committed, and hash-pinned (the anti-LARP property is pinning + provenance, not size).

**Selection rule (deterministic):** one image per merchant store, first-appearance index,
evenly spaced `k*(n-1)//19` over 317 distinct stores sorted by first appearance. Result:

| # | File | SHA256 (pinned) | Merchant (GT line 1) |
|---|---|---|---|
| 1 | img_0000.jpg | f9c8699bb1adcfa3a49cd8425057c1818b5b4ec62d003a6f8bd5b0af8d7ccd53 | OJC MARKETING SDN BHD |
| 2 | img_0022.jpg | 04d2d455b33fff097d2ea4ec595616ad622ebaab414a9a7b18a4c244cffb8616 | PASAR MINI JIN SENG |
| 3 | img_0052.jpg | e6349887bb90548cbb91656230944b061e0d7435cce037de1826fbff09aa09d3 | AEON CO. (M) BHD |
| 4 | img_0089.jpg | 525300601035f1ee41eccaa67a5d641e3a9491b3d37539242ce1834938326504 | CPI ROCKU SDN. BHD. |
| 5 | img_0115.jpg | c69bd2e6fa291bc6d44ce48bdcbfc57dd9b70445360b4cfeb0c6924c57140e34 | SEGI CASH & CARRY SDN. BHD. |
| 6 | img_0150.jpg | 6b10944345842f5acb281edee83424468647d30bb468275b991384ace9e09070 | SEMBOYAN TEGAS SDN BHD |
| 7 | img_0182.jpg | 01da0b4340014f54aac08322e2bcfb41f69ec4c6a9e12ee2979157b8baf2fe51 | FREEDOM OPTIMUM SDN BHD |
| 8 | img_0250.jpg | 64726e032c51813415c510c9368a571dd3e12685d2acfd1f043c08f8096c0b1b | MONSIEUR ( M ) SDN. BHD. |
| 9 | img_0302.jpg | 284a9a4e21fbd389a7a4acfd09cc28178fdec06bacb33a2c2084f8a6e80c7d18 | SUPER NINETY NINE SDN.BHD. |
| 10 | img_0345.jpg | 472f3f2e8be49ce33edee8a09d44932426fc2cfcd2fa4b50d2dd078b40a0454f | LIAN HING STATIONERY SDN BHD |
| 11 | img_0381.jpg | 39edcda02069bde170f8b72072a91accc41749e5793b10ef422ffa64d49981f4 | TASTE OF THE WORLD SDN BHD |
| 12 | img_0435.jpg | 62266d43a3b537e3c914b0190a33b5103ee573435fe5b18f0ec4808783213049 | T.A.S LEISURE SDN BHD (3-line GT) |
| 13 | img_0489.jpg | 3b8ae36fe4cd0be8689de1798128be2bd0bcff1f716435e514e4f02fd0b4e93b | MR . DAKGALBI SOLARIS |
| 14 | img_0542.jpg | 584a39304a80bb07563a3430078367b24a872a0ece95eed48015b38080e7d904 | Y SOON FATT S/B |
| 15 | img_0589.jpg | bee3f83eafce17942239b0221f65ac8cdab3e4e3e72fe6090044ee362c3694c0 | HASHA PETROKIOSK |
| 16 | img_0667.jpg | e978332d016259b6ee88cda163e81dd3f89edeede30a0f3a1fc75e3f66eaade5 | CHEF LEE SDN BHD |
| 17 | img_0721.jpg | cfe2e3fb11d9fb2091a4ed644c1d3e169d1ddaa105c7bfe55b25a339c8e8c4e8 | DIMILIKI OLEH T PLUS F&B SDN. BHD. |
| 18 | img_0818.jpg | 0996e7fbc5e074210149f23bbefbcae402a52bf3572194c90bc1394aedd638d1 | OGN GROUP SDN BHD |
| 19 | img_0883.jpg | bf7381430aa36bde6fae21fa8b22b2185667b5ca5358f7368ad1b90a686b3eca | RELAIS TOTAL OULMES |
| 20 | img_0963.jpg | a018b9efeb0a5d8c1f44d474bc77572d569c171a2ca13b19bfd44965574ffcf3 | SANJUNG REALITI SDN. BHD. |

**Fetch (Phase 1 only, one-time):** `scripts/fetch_golden20.py` — reuses the proven walk/normalize
logic of the old `scripts/download_data.py` (HF snapshot of `podbilabs/sroie-donut`, same
`img_NNNN.jpg` numbering), then **copies only the 20 pinned files** and hard-fails
(`DATA-ERR`, exit 2) on any SHA256 mismatch, missing file, or unexpected layout. Tests never
download; they read committed files and re-verify hashes at fixture setup (cheap, 20 files).

**Labels:** `data/golden/labels.json` — single JSON object `{filename: gt_text}` for the 20,
extracted verbatim from the verified `labels.jsonl` lines. Field order in GT text:
name / date / address / total (img_0435 has 3 lines — no address; keep as-is, it's real).

**Repo size gate:** total `data/golden/` after fetch ≤ 10 MB (EST. 5–10 MB; actual measured
and logged in Phase 1 — hard stop if exceeded, no proceeding on guess).

## 3. SUT + test layers

### 3.1 SUT (Flask, Python 3.12)

- `app/main.py` + `app/ocr_engine.py` (thin pytesseract wrapper: `image_to_data` output → response).
- Engine pin: **Tesseract 5.x** (`apt-get install tesseract-ocr` in CI; local v5.5.0 verified §1).
- Endpoints:
  - `POST /api/ocr` — multipart `image`. **LOCKED shape:**
    `{"text": str, "confidence": float 0..1, "boxes": [[x, y, w, h], ...]}`
    - `text`: full-page OCR text, newline-joined.
    - `confidence`: mean of per-word Tesseract confidences (words with conf ≥ 0 only) / 100, rounded 4dp; `0.0` when no words. (Single float per blueprint — replaces the old array.)
    - `boxes`: one `[left, top, width, height]` per word with conf ≥ 0.
  - `GET /health` — `{"status": "ok", "engine": "tesseract"}`.
  - `GET /` — the app UI. **Must mimic/copy the design of `docs/ui-reference/THIS_UI_EXAMPLE.jpg`** (user order 2026-09-14; spec + verification in §3.5). Functional elements required: upload control, extracted-text + confidence display, Clear control (UI-3).
- Errors: missing file → 400; non-image extension/MIME → 400; `MAX_CONTENT_LENGTH = 8 * 1024 * 1024` so an oversized upload → **413** (deterministic, asserted); server fault → 500.
- Requirements (exactly, no creep): `flask`, `pytesseract`, `pytest`, `requests`, `pillow`, `opencv-python-headless`, `pytest-html` (+ `playwright` dev-only in `tests/ui`). No paddle/onnxruntime/numpy-stack bloat. (Version pins fixed in Phase 1 from the actually-installed set — no invented pins; the 2026-09-12 `paddlepaddle-cpu`-404 failure, `WHYMUSESPARKISRETARDED.md:26-30`, is the precedent.)

### 3.2 Model quality oracles (the money layer)

**CER definition (locked) — field-anchored, because GT is 4 fields, not full text:**
normalize (NFKC, lowercase, collapse whitespace, strip non-alphanumerics except `.` in totals);
for each GT field find the best-matching OCR line by edit distance (pure-Python Levenshtein,
no extra dep); `CER = Σ edit_dist / Σ len(gt_field)` over the fields.
This is the same trap the old plan hit (`quality-gates.md:7-16`): CER against a 4-field GT
measures field fidelity. **Addendum 2026-09-14 (user order, Option C): the acceptance-CER
gates in the table below were placeholders and are superseded** — accuracy is telemetry,
stability is gated. The live gate spec = `docs/quality-gates.md`; its locked tolerances
change only via a new logged user order.

**Threshold oracles** (`tests/model/test_threshold.py`):

| ID | Case | Assertion (provisional) |
|---|---|---|
| MQ-T1 | 20 clean receipts | CER < 0.05 each; suite mean logged |
| MQ-T2 | heavy Gaussian blur (5×5, σ=2.0) | CER < 0.25 each (graceful degradation, no crash) |

**Metamorphic oracles** (`tests/model/test_metamorphic.py`) — relations, run in-memory:

| ID | Relation | Assertion |
|---|---|---|
| MQ-M1 | Rotation invariance | `norm(OCR(img)) == norm(OCR(rotate3deg(img)))` — primary, per blueprint. Calibrated fallback (logged if first run shows systematic word-segmentation drift): field-CER(pred_orig, pred_rot) ≤ 0.05 |
| MQ-M2 | Noise monotonicity | `CER(salt_pepper_2pct) ≤ CER(salt_pepper_15pct)` per image (degrade ⇒ error must not decrease) |
| MQ-M3 | Scale invariance | `CER(upscale_2x) ≤ CER(orig) + 0.01` per image |

**Invariant oracles** (`tests/model/test_invariant.py`) — must hold on every call:

| ID | Property |
|---|---|
| MQ-I1 | `0.0 ≤ confidence ≤ 1.0` |
| MQ-I2 | every box: `0 ≤ x, 0 ≤ y, x+w ≤ W, y+h ≤ H` |
| MQ-I3 | non-empty `text` on all 20 text-bearing receipts |

**Degradation (in-memory, seeded, deterministic):** cv2/Pillow transforms on the decoded
golden images — gaussian blur, salt-and-pepper noise (seeded `np.random.default_rng(42)`),
3° affine rotation (expand, white border), JPEG q20 (imencode/decode round-trip), 2× upscale
(INTER_CUBIC). Nothing written to disk. This is derivation of real images — consistent with
the surviving NO-LARP rule (transform real, never generate).

### 3.3 API layer (pytest + requests) — `tests/api/`

| ID | Case | Assertion |
|---|---|---|
| API-1 | POST clean receipt | 200, schema `{text:str, confidence:float, boxes:list[[int×4]]}`, `content-type: application/json` |
| API-2 | POST `.txt` fixture (`tests/fixtures/not-an-image.txt`, tiny non-OCR input — allowed) | 400 |
| API-3 | POST empty body / missing field | 400 |
| API-4 | POST 10 MB image | 413 |
| API-5 | `GET /health` | 200, `{"status":"ok","engine":"tesseract"}`, < 1 s |
| API-6 | latency, 5 runs on a clean receipt | mean < 1.5 s (Tesseract CPU ≈ 0.2–0.5 s per image — INFERRED from engine class; measured in Phase 1, logged) |
| API-7 | box/bounds spot-check on 5 receipts | boxes within image bounds (re-asserts MQ-I2 at API level) |

### 3.4 UI layer (Playwright, headless Chromium only, 3 tests max) — `tests/ui/`

| ID | Case |
|---|---|
| UI-1 | upload valid receipt → extracted text appears in DOM |
| UI-2 | upload invalid file → error message appears |
| UI-3 | Clear button resets form (file input + result area empty) |

TypeScript, `@playwright/test`, single `upload.spec.ts`, `chromium` project only.

### 3.5 UI visual spec — mimic the reference (user-ordered)

Reference image: `THIS_UI_EXAMPLE.jpg` (1200×1200, committed to `docs/ui-reference/`).
The SUT `GET /` page must mimic/copy this design. Spec **VERIFIED by vision pass
2026-09-14, user-confirmed** (the earlier "no image input" claim was corrected after the
user's config check — the model accepts image input).

**Reference design (what the sample shows):**
- Flat warm-gray page; the dashboard sits inside a large rounded light-lavender
  "monitor" frame with dark corners (device mockup); "Follow Me" + avatar, top right.
- Dark navy sidebar (left ~1/4, full height): darker **teal brand block** (circular
  photo avatar, name, email); menu with one **active light pill** (grid icon) + 3 plain
  items (person / gear / calendar icons), thin dividers; bottom: **light lavender card**
  with a date header + pencil icon, month label with chevrons, and a month grid with
  one date circled in **purple**.
- Main area (light): top row of **4 stat cards** — dark teal, **amber (the one accent
  card, 2nd position)**, dark teal, dark navy — each: label, big value,
  "Updated … ago" + arrow, white circular icon top-right. Middle row: left white
  "Observations" card (teal "View All"; rows with **circular progress rings "80%"**,
  name, timestamp, 5-star row, "N Days Left" chips; 3rd row adds an "Outcome
  Statistics" mini-block) + right white card with 5 rows (colored square icon, label,
  **progress bar** yellow/dark, % value). Bottom row: wide white "Stocks Graph" card
  (two smooth curves, **black + amber**, dark **tooltip bubble "4.5 Points"** at the
  peak, Jan–Dec axis) + right white card listing 4 rows (Google / Foursquare with
  colored square icons).

**QUACKO mapping (same skeleton, real content only):**

| Reference element | QUACKO element |
|---|---|
| Page + monitor frame | same (gray page, lavender rounded frame) |
| "Follow Me" + avatar | GitHub link (`github.com/AKARandy`) + mark |
| Teal brand block (avatar, name, email) | receipt-mark avatar, "QUACKO", "OCR · QA Suite" |
| Sidebar menu (active pill + 3) | Dashboard (active) / Upload / Reports / Evidence |
| Bottom lavender card (calendar) | "Last run" card: date + per-layer pass dots — real data from `data/baselines/metrics.json`; explicit "no run yet" state before |
| 4 stat cards (3 dark + 1 amber @2nd) | Total Receipts (20) / **Clean CER (amber)** / Avg OCR time (s) / Test pass rate — values = real run data only; `—` until a run exists |
| "Observations" card (rings, stars, chips) | upload + result: empty state = drop zone (dashed light box, receipt icon, browse, **Clear**); after upload = **confidence ring** + extracted text + words chip |
| Right card (5 icon+bar rows) | "Test Layers": API / Model / UI rows — square icon, name, pass-rate bar, % (real data / empty state) |
| "Stocks Graph" (2 curves + tooltip) | "CER by Receipt": clean vs degraded (blur) CER, 20 points, hover tooltip (real data / empty state) |
| Bottom-right list (Google/Foursquare) | "Evidence": GitHub Actions, GitHub Pages, Playwright report, pytest report — colored square icons + real URLs |

**Verification (NO-LARP):** every dashboard value = real measured run data
(`data/baselines/metrics.json`, written by the Phase-2 calibration) — no placeholder
numbers; pre-run state shows the explicit empty state. "Matches the reference" = vision
pass of the rendered UI vs the sample + user OK; proof artifact
`docs/screenshots/10-ui-match.png` (side-by-side, §5.1).

## 4. QA contract docs (adapt from existing, don't rewrite blind)

Existing drafts (`docs/test-strategy.md`, `defect-taxonomy.md`, `quality-gates.md`,
`test-cases.csv`) are rewritten for this scope: Tesseract risk profile (handwriting,
low-contrast, layout dependence), 3-layer pyramid, field-anchored CER, gate table =
§3.2/§3.3 assertions with **provisional** tag until first-run recalibration.

- `test-strategy.md` — scope, risks, pyramid, entry/exit criteria.
- `defect-taxonomy.md` — SUT-error (5xx/contract), model-error (gate miss), data-error
  (label vs image mismatch → verify by eye, fix label with recorded reason, never "fix" the test).
- `quality-gates.md` — merge gates: (1) 100% API pass, (2) clean CER < 5%, (3) zero
  invariant violations. Advisory: blur CER, latency, UI. Recalibration log section (date,
  order, before/after, measured basis) — same discipline as the old file.

## 5. CI/CD + evidence site

**`ci.yml` (on PR, BLOCKING):** ubuntu-latest → `sudo apt-get install -y tesseract-ocr` →
venv + `pip install -r requirements.txt` → start SUT, poll `/health` ≤ 60 s →
`pytest tests/api tests/model --html=report/api-model.html` → upload artifact.
Any failure blocks merge. Est. runtime 2–4 min (INFERRED: 20 imgs × ≤5 variants × ~0.3 s +
boilerplate; measured on first run and logged — not a promise).

**`deploy.yml` (on push to `main`):** all tests + Playwright (chromium) → failure-gallery
generation (only when model tests fail) → `mkdocs build` → deploy GitHub Pages to
`https://AKARandy.github.io/QUACKO/` (owner VERIFIED §1; repo created in Phase 4).

**Evidence site (mkdocs-material):**
1. `docs/` rendered (strategy, taxonomy, gates, index with status + badges).
2. `site/assets/reports/` — embedded pytest-html + Playwright HTML reports.
3. **Failure gallery (killer feature):** pytest hook (`pytest_runtest_makereport` in
   `tests/conftest.py`) on any model-quality failure writes
   `site/assets/failures/NN-<case>-<image>/` = `input.png` (clean or as-decoded),
   `degraded.png` (the variant that failed), `gt.txt`, `pred.txt`, `metrics.json`
   (CER + which assertion), `defect-class.txt` (per taxonomy). `scripts/gen_gallery.py`
   renders `docs/failure-gallery.md` from that directory (tables + images, grouped by
   defect class). Gallery page always exists; empty state = "no failures in latest run".

**Local parity:** everything in CI is runnable locally (venv + `python app.py` + pytest +
`npx playwright test`); Tesseract 5.5.0 verified present on this machine (§1).

### 5.1 Screenshot batch (proof — user-ordered, committed)

A batch of screenshots as proof, from **real runs only** — no mockups, no staged shots,
no reused V1 screenshots (none exist), OCR inputs always real golden receipts.
This agent captures them (the agent owns the whole chain, §7 Phase 4).

| # | File | Captures | Source |
|---|---|---|---|
| 01 | `01-upload-empty.png` | `GET /` UI, empty state (mimicked design) | SUT |
| 02 | `02-result-valid.png` | real receipt → extracted text + confidence in UI | SUT result state |
| 03 | `03-error-invalid.png` | `.txt` upload → error message in UI | SUT error state |
| 04 | `04-clear-reset.png` | after Clear: form + result area empty (UI-3) | SUT |
| 05 | `05-playwright-report.png` | Playwright HTML report, chromium, 3/3 pass | `playwright-report/` / site |
| 06 | `06-pytest-html.png` | pytest-html summary, API + Model | `report/` / site |
| 07 | `07-failure-gallery-sample.png` | ONE gallery entry side-by-side (input\|degraded\|GT\|pred\|class) — or the labeled empty state if the run is green | mkdocs site |
| 08 | `08-actions-green.png` | Actions runs: `ci.yml` (PR) + `deploy.yml` (main) green | github.com |
| 09 | `09-github-io-site.png` | Pages dashboard: index + reports + gallery | `AKARandy.github.io/QUACKO` |
| 10 | `10-ui-match.png` | rendered UI next to `THIS_UI_EXAMPLE.jpg` | side-by-side composite |

Rules (inherited from V1 §7, kept): PNG, 1280px window, <300 KB each, <3 MB total;
exact filenames; **committed** to `docs/screenshots/` (curated evidence — exempt from
gitignore, stays in the repo); no secrets/PII in frame (SROIE receipts are public
dataset images). `02` = hero, embedded in `docs/index.md`; the rest linked.

Timing: 01–04 + 10 captured locally just before the Phase-4 push (SUT running, browser
screenshot via agent-browser/Playwright); 05–07 after the first green `deploy.yml`
(from the live site); 08–09 after Pages is live. The batch is committed in the Phase-4
final commit, together with the badge-carrying index.

## 6. Repository layout (new tree)

```text
quacko/
├── .github/workflows/
│   ├── ci.yml                 # PR: API + Model (blocking)
│   └── deploy.yml             # main: + UI + mkdocs build + Pages
├── app/
│   ├── main.py                # Flask SUT
│   └── ocr_engine.py          # pytesseract wrapper
├── tests/
│   ├── api/                   # requests-based API tests
│   ├── model/                 # threshold / metamorphic / invariant
│   ├── ui/                    # Playwright specs (chromium)
│   ├── fixtures/not-an-image.txt
│   └── conftest.py            # data loading, hash verify, in-memory degradation, gallery hook
├── scripts/
│   ├── fetch_golden20.py      # one-time pinned fetch + SHA256 verify (DATA-ERR on mismatch)
│   └── gen_gallery.py         # failure gallery → docs/failure-gallery.md
├── data/golden/               # 20 committed images + labels.json + MANIFEST-20.sha256
├── docs/
│   ├── index.md               # status, badges, evidence links, hero screenshot
│   ├── test-strategy.md
│   ├── defect-taxonomy.md
│   ├── quality-gates.md
│   ├── failure-gallery.md     # GENERATED in CI
│   ├── ui-reference/THIS_UI_EXAMPLE.jpg   # UI spec reference (committed)
│   ├── screenshots/           # §5.1 proof batch 01–10 (committed, curated)
│   └── history/               # PLAN-V1.md, AGENTS-V1.md, NUKE.md, WHYMUSESPARKISRETARDED.md (gitignored evidence)
├── mkdocs.yml
├── requirements.txt
└── .gitignore                 # .venv/, site/, test-results/, playwright-report/, __pycache__/, .pytest_cache/, docs/history/
```

Migration mapping from current tree: `app.py`+`src/` → replaced by `app/`; old suites →
left on disk, not ported, not deleted (no delete orders in this plan); `data/golden/`
labels + manifest → source for the pinned 20; `docs/*` → rewritten in place for V2 scope;
`THIS_UI_EXAMPLE.jpg` → copied into `docs/ui-reference/`.
`git init` + first commit at Phase 1 end (repo was never a git repo — see §7 P1 exit).

## 7. Roadmap (each phase ends VERIFIED, not "done")

**Phase 0 — Paper (this file + decisions)** — DONE 2026-09-14
- [x] `PLAN-V2.md` written (this file).
- [x] AGENTS.md synced to V2 (Tesseract, committed-20, new response shape, nuke lock
      marked moot); original preserved as `docs/history/AGENTS-V1.md` (user order).
- [x] `PLAN.md`, `NUKE.md`, `WHYMUSESPARKISRETARDED.md` moved to `docs/history/`
      (gitignored per user order — evidence on disk, never in the repo).
- [x] NO-LARP layer re-confirmed with full §2b banned-fabrications text in AGENTS.md.
- [x] Screenshot batch (§5.1) + UI mimicry spec (§3.5) + agent-owned deploy chain
      (this Phase 4) added per user order 2026-09-14.
- Exit: satisfied — build may start at Phase 1.

**Phase 1 — Core SUT + data + API tests**
1. venv, install exact reqs, pin from `pip freeze` subset (no invented versions).
2. `scripts/fetch_golden20.py` run; 20 images + `labels.json` + `MANIFEST-20.sha256` in `data/golden/`; total size ≤ 10 MB (log actual).
3. `app/` SUT per §3.1; smoke by hand: health, one real upload, 400/413 paths.
4. `tests/api/` API-1…API-7; latency measurement logged (API-6 basis).
- Exit: `pytest tests/api` green locally with real Tesseract + real images; sizes + latency recorded; `git init` + first commit.

**Phase 2 — Model layer**
1. In-memory degradation helpers in `conftest.py` (seeded, §3.2).
2. CER implementation (field-anchored, §3.2) + `tests/model/` MQ-T/MQ-I.
3. **Calibration pass:** run MQ-T1 on all 20, log per-image CER table; set/recalibrate
   provisional gates from measured data (blueprint 5%/25% are starting values; if a clean
   receipt measurably exceeds 5%, the gate decision is explicit + logged, not a silent edit).
4. MQ-M1…M3; if MQ-M1 primary (strict equality) flakes systematically on real data,
   apply the logged fallback per §3.2.
- Exit: `pytest tests/api tests/model` green; calibration table + gate log committed.

**Phase 3 — UI + reports + site**
1. Implement `GET /` to mimic `THIS_UI_EXAMPLE.jpg` per the **vision-verified spec in
   §3.5** (reference read + user-confirmed 2026-09-14); copy the reference into
   `docs/ui-reference/`.
2. `tests/ui/` UI-1…3 (chromium headless) green locally.
3. pytest-html wired into both layers; Playwright HTML report.
4. mkdocs-material + `mkdocs.yml`; docs rewritten for V2 (§4); local `mkdocs build` clean.
- Exit: full local run green: API + Model + UI + `mkdocs build`; UI visual match
  confirmed per §3.5 (vision pass or user OK) — otherwise this phase is NOT done.

**Phase 4 — Automation + gallery + deploy (this agent owns the whole chain)**

User order 2026-09-14: the agent does **repo creation → commits → GitHub CI/CD →
GitHub.io deployment** end-to-end. `gh` is authenticated as **AKARandy** (VERIFIED §1,
scopes `repo` + `workflow` — sufficient for create/push/trigger; Pages deploys via
`actions/deploy-pages` with `id-token`, no extra token scope needed).

1. `ci.yml` + `deploy.yml` per §5.
2. `gen_gallery.py` + failure hook; force one real failure locally (e.g. temp gate
   CER < 0.01) to prove the gallery captures artifacts — then restore the gate and
   re-run green.
3. Screenshot batch 01–04 + 10 (§5.1) captured locally before push.
4. `gh repo create AKARandy/QUACKO --public` (public = portfolio proof; if the user
   wants private, say so before this runs) → push `main`.
5. Open a small follow-up PR (e.g. a docs fix) so `ci.yml` runs on PR and its blocking
   behavior is real evidence, not assumption → merge to main.
6. Watch `ci.yml` + `deploy.yml` to completion. On failure: fix, re-push, and report
   the failure honestly — nothing is "green" until both are actually green.
7. Pages live → capture 05–09 from the live site + Actions page (§5.1).
8. Final commit: screenshot batch + index with real badges + any gallery updates;
   push; verify Pages redeploys with the batch.
- Exit: `https://AKARandy.github.io/QUACKO/` serves index + reports + gallery;
  `docs/screenshots/` (01–10, real runs) committed; index carries real badges;
  anything not green is named as such in the index, not hidden.

## 8. Risks & open items (named, not buried)

1. **Tesseract quality on these receipts is UNMEASURED.** All §3.2 gates are provisional
   until Phase 2 calibration. If clean CER lands ≥ 5% on some images, options (pick better
   20, adjust gate with logged order, pre-process) are decisions for that moment — no
   silent tuning. (Tesseract is weaker than the RapidOCR PP-OCRv4 it replaces; the
   tradeoff is ~13 s → ~0.3 s per inference, per old measured values — INFERRED transfer.)
2. **MQ-M1 strict equality** may be brittle for tilted receipts; fallback pre-defined §3.2.
3. **10 MB image for API-4** must be a real image file (not a renamed .txt) — generate by
   JPEG-encoding a real golden image upscaled, in-test, in-memory (derivation, allowed).
4. **CI apt install latency** (tesseract-ocr) — ubuntu-latest caches it; still adds ~30 s.
5. **AGENTS.md drift** — mitigated (synced 2026-09-14, §0); re-check if this plan changes
   again, since the binding file must track it.
6. **No repo yet** — owner is known (AKARandy, §1) but the repo doesn't exist until
   Phase 4; until then, "green" means local, and reports say so.
7. **UI vision gap — RESOLVED 2026-09-14.** Model accepts image input (user-verified
   config; earlier "no image input" claim was wrong). Reference read via vision pass +
   user-confirmed (§3.5). Residual risk: exact font/spacing fidelity — covered by shot
   10 side-by-side + user check before Phase 3 closes.
8. **Screenshot capture tooling** — needs a browser (agent-browser or Playwright) against
   the local SUT and the live Pages/Actions pages. Capture failure → report it; never
   substitute mockups or stale images.

## 9. Honesty (claim labels)

- **VERIFIED this session:** §1 facts (incl. `gh auth` = AKARandy, `THIS_UI_EXAMPLE.jpg`
  1200×1200 present); the 20-image pins + hashes in §2 (read from `labels.jsonl` +
  `MANIFEST.sha256`).
- **INFERRED (steps shown):** §3.5 UI layout/palette (heuristic luminance-map rendering +
  color histogram of the sample — not visual inspection); §3.3 API-6 latency class;
  §5 CI runtime estimate; §8.1 speed tradeoff.
- **PLANNED (nothing built):** every artifact in §3–§7, all workflows, the site, the
  repo itself, all "green" outcomes. Gate values = provisional blueprint numbers, not
  measurements.
- Pre-report gate (inherited `PLAN.md` §8.5) applies to every phase exit: real data?
  real engine? numbers from actual runs? failures disclosed? scope exact (local vs CI)?
