# Test Strategy — QUACKO V2

## Scope

- **SUT:** Flask 3 + Tesseract 5 (`pytesseract`), `POST /api/ocr`, `GET /health`, `GET /`.
- **Out of scope (deliberate, PLAN-V2 §0):** Selenium, RestAssured, Postman/Newman,
  JMeter, GPU/CUDA, handwritten-text support.

## Data

Real data only. The **Committed 20**: 20 real SROIE Task-1 receipts from
`podbilabs/sroie-donut`, SHA256-pinned, committed to `data/golden/` (provenance in
`data/golden/PROVENANCE-20.md`). Ground truth = 4 key fields per receipt
(merchant name, date, address, total) — which is why all CER oracles are
**field-anchored** (see Quality Gates). Degradation (blur, noise, rotation, JPEG,
scale) is applied **in-memory** with seeded RNG in test fixtures — derivation of
real images, never synthetic generation. Missing file or hash mismatch = hard
`DATA-ERR`, never substitution.

## Test pyramid

| Layer | Tool | What it proves | Blocking? |
|---|---|---|---|
| Model quality | pytest + real Tesseract | invariants + metamorphic relations (hard), CER telemetry (reported), 10% regression (hard) | yes (PR) |
| API contract | pytest + requests | schema, 400/413 paths, latency < 1.5 s, box bounds | yes (PR) |
| UI smoke | Playwright (chromium headless) | upload → text in DOM; invalid → error; Clear resets | yes (main deploy) |
| Evidence | pytest-html + Playwright HTML + failure gallery | a human can see every result and every real miss | published on Pages |

## Risks

1. **Tesseract is a general OCR engine**, not receipt-specialized: layout dependence,
   low contrast, dense small print, and date/total digit errors are the expected
   failure modes. Mitigation: field-anchored CER measures what matters (the 4 fields),
   and the failure gallery keeps every miss visible instead of averaging it away.
2. **Accuracy is telemetry, stability is gated** (Option C, user order 2026-09-14):
   CER is measured and displayed every run; hard gates cover contract / invariants /
   metamorphic / regression. Locked tolerances (M1 0.20, M3 +0.10, M2 aggregate
   strict, REG 10% + 0.01 floor) change only via an explicit logged user order
   (Quality Gates §change log; re-baseline procedure for environment deltas).
3. **Single-CPU timing** (API-6 latency): CI runners differ from local hardware; the
   gate is measured per environment and logged, not assumed.
4. **Metamorphic strictness** (MQ-M1 rotation): 3° tilt can change word segmentation;
   a pre-defined, logged fallback bound exists (see Quality Gates).

## Entry / exit criteria

- **Entry:** venv + pinned deps installed; Tesseract on PATH; Committed 20 hash-verified.
- **Exit (per run):** all blocking tests pass on real data with a real engine; failures
  (if any) classified per Defect Taxonomy with gallery entries; measured numbers logged
  (CER table, latency, pass rates) — nothing reported green without those artifacts.
