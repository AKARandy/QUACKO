# QUACKO

Multi-layer QA suite for a **real** OCR SUT: Flask + Tesseract 5, the **Committed 20**
(SHA256-pinned real SROIE receipts, in-repo), in-memory seeded degradation, and a
failure gallery that shows exactly *how* the model fails.

> **Honesty rule (binding):** every number on this site comes from a logged real run
> (see [Quality Gates](quality-gates/)). No placeholder metrics, no stub engine, no
> hidden failures. Pre-run dashboard states say "no run yet" — they never invent numbers.

## CI

| Workflow | Purpose | Status |
|---|---|---|
| [`ci.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/ci.yml) | PR: API + Model (blocking) | — |
| [`deploy.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/deploy.yml) | main: + UI + site build + Pages | — |

## Architecture

```text
Committed 20 (real SROIE receipts, SHA256-pinned, committed in-repo)
  -> Flask SUT: POST /api/ocr · GET /health · GET / (mimics the reference dashboard UI)
      -> pytest (API): contract / negative / 413 / latency / bounds
      -> pytest (Model): threshold (field-CER) / metamorphic / invariant oracles
      -> Playwright (chromium): UI smoke x3
  -> artifacts: pytest-html + Playwright HTML + failure gallery (real misses only)
  -> mkdocs-material site (this page) on GitHub Pages
```

## Evidence

- [Failure Gallery](failure-gallery/) — captured misses: input | degraded | GT | pred | defect class
- [API + Model report (pytest-html)](reports/api-model.html) — generated in CI
- [UI report (Playwright HTML)](reports/ui-report/index.html) — generated in CI
- [Repository](https://github.com/AKARandy/QUACKO) · [Actions](https://github.com/AKARandy/QUACKO/actions)

## Screenshot proof (real runs)

Curated batch in `docs/screenshots/` (01–10), captured from real local/CI runs.
Hero: `02-result-valid.png` — a real receipt through the real engine.

## Data & gates

- 20 real receipts, 20 different merchants, pinned in `data/golden/MANIFEST-20.sha256`
  with full provenance (`data/golden/PROVENANCE-20.md`). Tests re-verify every hash on load.
- Gates enforced in-code (pytest asserts); provisional values are recalibrated after the
  first full run and every change is logged in [Quality Gates](quality-gates/).
