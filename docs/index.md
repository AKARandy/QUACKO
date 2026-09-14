# QUACKO

Multi-layer QA suite for a **real** OCR SUT: Flask + Tesseract 5, the **Committed 20**
(SHA256-pinned real SROIE receipts, in-repo), in-memory seeded degradation, and a
failure gallery that shows exactly *how* the model fails.

> **Honesty rule (binding):** every number on this site comes from a logged real run
> (see [Quality Gates](quality-gates.md)). No placeholder metrics, no stub engine, no
> hidden failures. Pre-run dashboard states say "no run yet" — they never invent numbers.

## Status (honest, per NO-LARP)

**VERIFIED 2026-09-14 (local: Windows-11 / Tesseract 5.5.0.20241111 / Python 3.12.6):**
all hard gates green — API 7/7 · invariants 3/3 · metamorphic 3/3 (M1 ≤ 0.20,
M2 aggregate strict, M3 + 0.10) · regression 2/2 vs committed baseline · UI 3/3.

**Accuracy telemetry (reported, not gated):** field-CER clean mean **0.078**,
blur mean **0.098** (per-receipt table below, measured every run). Tesseract 5 is a
general-purpose engine — field accuracy is shown as telemetry; the gates guarantee
contract, invariants, stability, and non-regression ([Quality Gates](quality-gates.md),
Option C spec).

**PLANNED:** GitHub repo `AKARandy/QUACKO`, CI, and this site on GitHub Pages.
Badges below go live once the repo exists — they are not evidence yet. The CI
environment (ubuntu + apt Tesseract) has a different provenance than the local
baseline; the documented re-baseline procedure covers that (Quality Gates §re-baseline).

## CI

| Workflow | Purpose | Status |
|---|---|---|
| [`ci.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/ci.yml) | PR: API + Model hard gates (blocking) | — |
| [`deploy.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/deploy.yml) | main: + UI + site build + Pages | — |

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
