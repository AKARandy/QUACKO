<div class="qk-hero" id="qk-dash">
  <h1 class="qk-title">QUACKO</h1>
  <p class="qk-sub">QA dashboard for a Tesseract OCR receipt reader. Every widget below is fed by the latest logged CI run. Full spec: <a href="quality-gates/">Quality Gates</a>.</p>
  <div class="qk-pills">
    <span class="qk-pill" id="pill-api" data-label="API CONTRACT">API CONTRACT: LOADING</span>
    <span class="qk-pill" id="pill-model" data-label="MODEL GATES">MODEL GATES: LOADING</span>
    <span class="qk-pill" id="pill-ui" data-label="UI SUITE">UI SUITE: LOADING</span>
    <span class="qk-pill" id="pill-cer" data-label="CER TELEMETRY">CER TELEMETRY: LOADING</span>
  </div>
  <div class="qk-grid">
    <div class="qk-card"><div class="qk-num" id="m-receipts">--</div><div class="qk-label">Total receipts</div></div>
    <div class="qk-card"><div class="qk-num" id="m-clean">--</div><div class="qk-label">Clean CER mean</div></div>
    <div class="qk-card"><div class="qk-num" id="m-blur">--</div><div class="qk-label">Blur CER mean</div></div>
    <div class="qk-card"><div class="qk-num" id="m-reg">--</div><div class="qk-label">Regression status</div></div>
  </div>
  <p class="qk-src" id="dash-src">Loading run data...</p>
</div>

<div class="qk-chart-wrap">
  <h2>Clean vs blur CER per receipt</h2>
  <div class="qk-chart-box" id="cer-box"><canvas id="cer-chart"></canvas></div>
  <p class="qk-note">Field-CER per receipt (percent). CER is telemetry here: measured and shown, never a pass/fail gate. <a href="failure-gallery/">Failure gallery</a> · <a href="reports/api-model.html">pytest report</a> · <a href="reports/ui-report/">Playwright report</a></p>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

## CI

| Workflow | Purpose | Status |
|---|---|---|
| [`ci.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/ci.yml) | PR: API + Model hard gates (blocking) | [![CI](https://github.com/AKARandy/QUACKO/actions/workflows/ci.yml/badge.svg)](https://github.com/AKARandy/QUACKO/actions/workflows/ci.yml) |
| [`deploy.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/deploy.yml) | main: + UI + site build + Pages | [![Deploy](https://github.com/AKARandy/QUACKO/actions/workflows/deploy.yml/badge.svg)](https://github.com/AKARandy/QUACKO/actions/workflows/deploy.yml) |

## Architecture

```text
Committed 20 (real SROIE receipts, SHA256-pinned, committed in-repo)
  -> Flask SUT: POST /api/ocr · GET /health · GET / (mimics the reference dashboard UI)
      -> pytest (API): contract / negative / 413 / bounds (latency = telemetry)
      -> pytest (Model): invariants · metamorphic (hard) · CER telemetry · regression (hard)
      -> Playwright (chromium): UI smoke x3
  -> artifacts: pytest-html + Playwright HTML + failure gallery (real misses only)
  -> mkdocs-material site (this page) on GitHub Pages
```

## Evidence

- [Failure Gallery](failure-gallery.md) — captured hard-gate misses: input | degraded | GT | pred | defect class
- [API + Model report (pytest-html)](reports/api-model.html) — generated in CI
- [UI report (Playwright HTML)](reports/ui-report/index.html) — generated in CI
- [Repository](https://github.com/AKARandy/QUACKO) · [Actions](https://github.com/AKARandy/QUACKO/actions)

## Screenshot proof (real runs)

Curated batch in `docs/screenshots/` (01–11), captured from real local/CI runs.
Hero: `02-result-valid.png` — a real receipt through the real engine.
`11-gallery-proof.png` is the gallery self-test: M1 was temporarily tightened
(0.20 → 0.0001), the failure was captured and rendered, then the bound was
restored and the suite re-ran green (raw artifacts kept on disk under
`docs/assets/gallery-proof/`).

## Data & gates

- 20 real receipts, 20 different merchants, pinned in `data/golden/MANIFEST-20.sha256`
  with full provenance (`data/golden/PROVENANCE-20.md`). Tests re-verify every hash on load.
- Three tiers, enforced in code (pytest asserts): **hard gates** (contract, invariants,
  metamorphic, regression) · **accuracy telemetry** (CER measured + displayed, never
  gated) · **regression baselines** (10% relative, provenance-matched; REG fails
  closed on unknown environments). Every change is
  logged in [Quality Gates](quality-gates.md).
