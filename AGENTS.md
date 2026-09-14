# AGENTS.md — QUACKO (V2 — Tesseract edition)

Source of truth: `PLAN-V2.md`. If it conflicts with a guess, trust `PLAN-V2.md`.
V1 rules (RapidOCR, full-973, nuke lock) are SUPERSEDED by explicit user order 2026-09-14;
originals preserved in `docs/history/` (gitignored, evidence only).

## Hard rules (never violate)

- **Real Tesseract 5 only** (pytesseract wrapper over system/CI Tesseract 5.x). No stub/fake/mock OCR fallback — fail fast if engine missing. (Local: `C:\Program Files\Tesseract-OCR\tesseract.exe` v5.5.0, VERIFIED 2026-09-14; CI: `apt-get install tesseract-ocr`.)
- **Real data only, NO LARP, NEVER synthetic.** No PIL-generated text images anywhere, not even as fallback. Test inputs = the **Committed 20**: 20 real SROIE Task-1 receipts, SHA256-pinned in `PLAN-V2.md` §2, committed to `data/golden/` with `labels.json` + `MANIFEST-20.sha256`. The subset is explicit and pinned — never a silent one. In-memory degradation (conftest) may only *transform* these real images (seeded; nothing written to disk). Missing file or hash mismatch → fail fast (`DATA-ERR`), never substitute, never regenerate.
- **Tiny non-OCR fixtures** (e.g. `.txt` for negative upload test) are allowed; they are not OCR data.

## Nuke lock — RESOLVED 2026-09-14 (moot under V2)

The V1 §6.4 / `NUKE.md` delete lock no longer applies: the V2 repo is ~10 MB of source +
pinned data with no heavy local installs to delete. No delete commands are authorized or
planned; `docs/history/NUKE.md` is evidence only. Do not resurrect the lock, and do not run
bulk deletes without a fresh, explicit user order.

## NO-LARP (binding, no exceptions)

- No synthetic data as real (even as fallback), no stubs reported as genuine, no invented metrics/URLs/results, no silent subsetting, no buried failures, no agent-invented composite scores.
- Banned fabrications (§2b): no agent-invented composite index, weighted sum, "overall score," ranking, or derived metric whose formula/weights/inputs the agent itself made up (e.g. `quality = 0.4*accuracy + 0.6*vibes`, blended gate numbers). Citing a real published index with source + date is fine. No metric value without the real measured inputs behind it. Only exception: a cited, pre-existing definition (spec/doc/standard, quoted) computed from real measured inputs — formula + inputs + raw output shown. Definition first, numbers second, never reversed. Rule of thumb: if you cannot point to where the formula was defined before you computed it AND to the real run that produced each input, it is made up — delete it and report raw measurements.
- Evidence before synthesis: read the file / run the command yourself, cite `file:line` or output. Evidence beats speculation; correct rather than falsely agree.
- Fail fast on missing data/model/dependency: name what's missing and where; never substitute or extrapolate past the failure.
- Tag factual claims: **VERIFIED** (read/ran this session) / **INFERRED** (show steps) / **PLANNED** (not done, no success implied). Gate architecture (Option C, user order 2026-09-14): **accuracy = telemetry** (CER measured + displayed, never pass/fail); **stability = hard gates** (API contract, invariants, metamorphic relations, 10% regression vs the provenance-matched committed baseline entry). Live spec + change log = `docs/quality-gates.md`. The `baselines` entries of `data/baselines/metrics.json` move ONLY via `scripts/calibrate.py` / `scripts/add_baseline.py` + commit under a logged user order; REG selects by (os_family, tesseract_version) and fails closed with ENV-DELTA if no entry matches — never by silently editing gates or baselines.
- Pre-report gate before any "done/green/passing": real data? real system? numbers from actual runs? failures disclosed? scope exact (local vs CI, which commit)? Any no → report says so first.

## Toolchain quirks

- Windows PowerShell 5.1. Chain with `; if ($?) { ... }`, quote paths, use `workdir` param — never `cd`.
- Python 3.12 via `.venv` (`python -m venv .venv`). Tesseract 5.x on PATH locally (v5.5.0 verified); CI is ubuntu-latest + `apt-get install tesseract-ocr`. No Java/Maven/Node-JMeter in V2 scope — do not reintroduce without user order.
- Flask response shape (locked, V2): `POST /api/ocr` → `{text: str, confidence: float 0..1, boxes: [[x,y,w,h]]}`; `GET /health` → `{status:"ok", engine:"tesseract"}`; oversized upload → 413 (`MAX_CONTENT_LENGTH = 8 MiB`).
- Dataset: committed in-repo (`data/golden/` = 20 images + `labels.json` + `MANIFEST-20.sha256`). `scripts/fetch_golden20.py` is one-time, pin-verified, `DATA-ERR` on mismatch; tests never download.
- CI: 2 workflows — `ci.yml` (PR: API + Model, blocking) + `deploy.yml` (main: + Playwright UI + mkdocs build + GitHub Pages). Thresholds enforced in-code (pytest asserts).
- `docs/history/` is gitignored — V1 evidence, not repo state; never cite it as current rules.
