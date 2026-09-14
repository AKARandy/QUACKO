# Quality Gates — QUACKO V2 (Option C architecture, locked 2026-09-14)

Standard ML-QA split: **accuracy is telemetry, stability is gated.** Absolute
field-CER is measured every run and displayed — never pass/fail. Pass/fail gates
cover the API contract, invariants, behavioral stability (metamorphic relations),
and non-regression against a committed, provenance-stamped baseline.

## CER definition (locked)

GT is 4 key fields per receipt, not full text. `CER = Σ ed / Σ len(field)` where
`ed` = min over OCR line groups (1–3 consecutive lines, space-joined, group ≤ 5×
field length) of the **semi-global edit distance** between the normalized GT field
(NFKC, lowercase, alphanumerics + `.` kept) and any substring of the group
(`tests/model/cer.py`, pure-Python Levenshtein, no extra dependency). Semi-global
matching means extra OCR content around a correctly read field (timestamps after
dates, column labels around totals) does not penalize it; a field absent from the
OCR output costs its full length.

## Tier 1 — Hard gates (pass/fail; block CI)

| Gate | Assertion | Tolerance | Status (local 2026-09-14) |
|---|---|---|---|
| API-1..5,7 | exact schema `{text, confidence, boxes}`; `.txt` → 400; missing file → 400; > 8 MiB → 413; health dict < 1 s; box bounds on 5 receipts | strict | PASS 7/7 |
| API-6 | latency — **TELEMETRY** (measured + logged to `data/baselines/api-latency.json`; the gate is the contract itself: 200 on all 5 real POSTs) | — | PASS (mean ≈ 0.55 s) |
| MQ-I1..I3 | confidence ∈ [0,1]; boxes within original W×H; non-empty text on all 20 | strict | PASS 3/3 |
| MQ-M1 | rotation stability: `norm(text)` equal, else field-CER(clean, rotated 3°) ≤ 0.20 | **0.20 (locked)** | PASS (worst 0.1454) |
| MQ-M2 | **aggregate** noise monotonicity: Σ CER(15% sp) ≥ Σ CER(2% sp) over all 20 | strict | PASS (11.2355 ≥ 6.389) |
| MQ-M3 | scale stability: CER(2× upscale) ≤ CER(orig) + 0.10 | **+0.10 (locked)** | PASS (worst +0.0583) |
| UI-1..3 | upload → text in DOM; invalid → error; Clear resets (chromium headless; deploy tier) | strict | PASS 3/3 |
| REG-1/2 | per-receipt clean & blur CER ≤ max(0.01, 1.10 × baseline) | 10% + floor | PASS (0% delta vs baseline) |

**Locked tolerances, basis, and change rule.** Change only via a new logged user
order in the change log below:

- **M1 ≤ 0.20** — measured worst 0.1454 (2026-09-14, local) + ~38% headroom.
  Tesseract is not pixel-stable under 3° rotation; gated deskew mitigates, the
  residual is engine behavior.
- **M3 ≤ +0.10** — measured worst +0.0583 + ~71% headroom.
- **M2 strict aggregate (no tolerance)** — a discrete segmentation engine cannot
  contractually promise per-receipt monotonicity (measured per-receipt decreases:
  4/20, max −0.2086 on img_0250 — visible as telemetry every run); the aggregate
  holds with 1.76× margin (11.2355 vs 6.389).
- **REG floor 0.01** — labeled JUDGMENT parameter: covers receipts with a zero
  baseline where "10% of zero" is undefined. The 10% relative factor is per the
  user order.

## Tier 2 — Accuracy telemetry (measured + displayed; no pass/fail)

- Per-receipt field-CER — clean, heavy blur, 3° rotation, noise 2% / 15%, 2×
  upscale — every run → `report/cer-run.json` → `metrics.json` `last_run` →
  dashboard chart + per-receipt table.
- Means, M2 aggregate sums, and **provenance** (OS family, Tesseract version,
  Python, pipeline string) every run.
- `tests/model/test_cer_telemetry.py` asserts measurement **integrity** only
  (20/20 measured, every CER ∈ [0,1]). A failure there = broken pipeline or data
  (DATA-ERR class) — never a statement about engine accuracy.

## Tier 3 — Regression baseline

- File: `data/baselines/metrics.json`, `baseline` section (schema 2), committed.
- Rule: `run_cer ≤ max(0.01, 1.10 × baseline_cer)`, per receipt, clean + blur
  (`tests/model/test_regression.py`).
- Provenance is recorded in both sections, so an environment delta is diagnosable.
- The `baseline` section is written **only** by `scripts/calibrate.py` + commit
  under a logged order. A run never touches it (`scripts/log_run.py` writes
  `last_run` only).

### Re-baseline procedure (environment correction — user addendum 2026-09-14)

1. **Trigger:** REG red + provenance mismatch (Tesseract version, OS family, or
   pipeline) between current run and baseline + no code change since the baseline
   commit.
2. **Verify:** the failure message carries the ENVIRONMENT DELTA diagnostic;
   `git log <baseline-commit>..HEAD` is empty or contains no SUT/data changes.
3. **Fix:** pull `data/baselines/metrics.json` + `report/cer-run.json` from the CI
   artifact (`test-reports`), record the order in the change log, commit the new
   `baseline` section with its provenance. This is an **environment correction,
   not a burying event** — the old baseline and its numbers remain in this log.
4. **Expectation:** the first CI run (ubuntu apt Tesseract vs the local 5.5.0
   baseline) is a different provenance; an environment-delta REG red there is
   anticipated and pre-authorized by this procedure.

## Baseline register

| # | Date | Provenance | clean mean | blur mean | Order |
|---|---|---|---|---|---|
| 1 | 2026-09-14 | windows / Tesseract 5.5.0.20241111 / python 3.12.6 / `gray+normalize(1600-2400)+gated-deskew+psm6` | 0.0780 | 0.0977 | initial baseline — Option C order (measured run `2026-09-14T10:53:38Z`, 120 real OCR calls, avg 1.136 s) |

## Change log

- **2026-09-14** — gates initialized at blueprint provisional values (0.05 / 0.25 /
  ≤0.05 / strict / +0.01 / 1.5 s). First full measurement (local, Tesseract 5.5.0):
  clean mean 0.086 worst 0.222, blur mean 0.114 worst 0.687 — the Tesseract-only SUT
  is structurally above the placeholder acceptance numbers.
- **2026-09-14 (user order, Option C)** — spec re-derivation: acceptance-CER gates
  (0.05 / 0.25) removed as arbitrary blueprint placeholders; accuracy → telemetry;
  stability → hard gates (M1 0.05 → **0.20**, M3 +0.01 → **+0.10**, both with the
  measured basis above; M2 per-receipt strict → **aggregate strict**); API-6 latency
  demoted to telemetry; 10% relative regression gate + 0.01 floor added; baseline
  schema 2 with provenance (addendum). Before → after:
  `0.05 / 0.25 / ≤0.05 / strict-per-receipt / +0.01 / 1.5s-hard`
  → `(no CER acceptance) / 0.20 / aggregate-strict / +0.10 / 10%-regression / latency-telemetry`.
- _pending — first CI run: if REG reds with provenance mismatch, baseline register
  entry #2 per the procedure above._
