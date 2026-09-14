# Quality Gates — QUACKO V2

Gates are enforced **in code** (pytest asserts). A threshold miss is a release
blocker, not a tune-the-gate exercise: gates change only via an explicit, logged
decision below.

## CER definition (locked)

GT is 4 key fields per receipt, not full text. `CER = Σ ed / Σ len(field)` where
`ed` = min over OCR line groups (1–3 consecutive lines, space-joined, group ≤ 5×
field length) of the **semi-global edit distance** between the normalized GT field
(NFKC, lowercase, alphanumerics + `.` kept) and any substring of the group
(`tests/model/cer.py`, pure-Python Levenshtein, no extra dependency). Semi-global
matching means extra OCR content around a correctly read field (timestamps after
dates, column labels around totals) does not penalize it; a field absent from the
OCR output costs its full length.

## Blocking gates (PR: `ci.yml`)

| Gate | Assertion | Source | Status |
|---|---|---|---|
| MQ-T1 | clean receipt CER < 0.05, all 20 | `test_threshold.py` | **provisional** — recalibrate after first full run |
| MQ-T2 | heavy-blur (5×5, σ=2.0) CER < 0.25, all 20 | `test_threshold.py` | **provisional** — recalibrate after first full run |
| MQ-M1 | 3° rotation: normalized text equal; fallback field-CER(pred_orig, pred_rot) ≤ 0.05 if strict equality flakes systematically | `test_metamorphic.py` | provisional (fallback pre-defined, logged if used) |
| MQ-M2 | noise monotonicity: CER(15% sp) ≥ CER(2% sp) per image | `test_metamorphic.py` | strict (blueprint) |
| MQ-M3 | scale: CER(2× upscale) ≤ CER(orig) + 0.01 per image | `test_metamorphic.py` | strict (blueprint) |
| MQ-I1..I3 | confidence ∈ [0,1]; boxes within image bounds; non-empty text on all 20 | `test_invariant.py` | strict (invariants — any violation is critical) |
| API-1..7 | schema `{text, confidence, boxes}`; `.txt` → 400; missing → 400; 10 MB → 413; health < 1 s; mean latency < 1.5 s (5 real POSTs, logged to `data/baselines/api-latency.json`); box bounds on 5 receipts | `test_api.py` | strict (contract) |

## Blocking (main: `deploy.yml`)

| Gate | Assertion |
|---|---|
| UI-1..3 | upload → text in DOM; invalid → error shown; Clear resets form (chromium headless) |

## Advisory (never blocks)

- Blur degradation quality beyond MQ-T2 (visible in gallery + CER chart).
- Dashboard pass-rate trend over runs (`data/baselines/metrics.json`).

## Recalibration log

Format: date · order (who/what) · before → after · measured basis (run + numbers).
Tighten, never silently loosen.

- _2026-09-14 — gates initialized at blueprint values (0.05 / 0.25 / 1.5 s); awaiting
  first full calibration run (Phase 2) to log measured values._
