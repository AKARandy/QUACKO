# QUACKO — V2 (Tesseract edition)

Multi-layer QA suite for a **real** OCR SUT: Flask 3 + Tesseract 5 behind
`POST /api/ocr`, tested against the **Committed 20** — 20 real SROIE Task-1
receipts, SHA256-pinned and committed in-repo (`data/golden/`). No synthetic
data, no stub engine, no hidden failures: every number on the evidence site
comes from a logged real run.

**Source of truth:** `PLAN-V2.md`. **Agent rules:** `AGENTS.md`.

## Layers

| Layer | Tool | What it proves |
|---|---|---|
| Model quality | pytest + real Tesseract | field-CER threshold, metamorphic (rotation/noise/scale), invariant oracles |
| API contract | pytest + requests | exact response schema, 400/413 paths, latency < 1.5 s, box bounds |
| UI smoke | Playwright (chromium headless) | upload → text in DOM; invalid → error; Clear resets |
| Evidence | pytest-html + Playwright HTML + failure gallery | every result and every real miss, visible |

## Status (honest, per NO-LARP)

- **VERIFIED 2026-09-14 (local, Windows, Tesseract 5.5.0):** API 7/7 pass,
  UI 3/3 pass, invariants 3/3 pass; threshold + metamorphic gates measured on
  all 20 receipts — see `docs/quality-gates.md` (recalibration log) and
  `data/baselines/metrics.json` for the real per-receipt table.
- **PLANNED:** GitHub repo `AKARandy/QUACKO`, CI (`ci.yml` PR-blocking,
  `deploy.yml` main + GitHub Pages at `AKARandy.github.io/QUACKO/`).
  Badges below go live once the repo exists — they are not evidence yet.

| Workflow | Badge |
|---|---|
| [`ci.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/ci.yml) | [ci](https://github.com/AKARandy/QUACKO/actions/workflows/ci.yml/badge.svg) |
| [`deploy.yml`](https://github.com/AKARandy/QUACKO/actions/workflows/deploy.yml) | [deploy](https://github.com/AKARandy/QUACKO/actions/workflows/deploy.yml/badge.svg) |

## Quickstart (local)

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python scripts\fetch_golden20.py   # one-time; SHA256-pinned, DATA-ERR on mismatch
.venv\Scripts\python app\main.py                 # SUT on :5000 (needs Tesseract 5 on PATH)
.venv\Scripts\python -m pytest tests\api tests\model -v
cd tests\ui; npm ci; npx playwright install chromium; npx playwright test
```

`data/golden/` is committed, so a fresh clone skips the fetcher entirely
(its hashes are re-verified on every test load).

## Docs

- `docs/index.md` — evidence site home (mkdocs-material, GitHub Pages)
- `docs/test-strategy.md` · `docs/defect-taxonomy.md` · `docs/quality-gates.md`
- `docs/test-cases.csv` — 18 test cases, oracle + gate + last status
- `docs/ui-reference/THIS_UI_EXAMPLE.jpg` — UI spec reference (mimic target)
- `docs/history/` — V1 evidence (gitignored, not repo state)
