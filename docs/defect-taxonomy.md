# Defect Taxonomy — QUACKO V2

Every failure gets exactly one class. The class decides who fixes what — and what
the failure gallery shows.

## Classes

| Class | Definition | Example | Fix owner |
|---|---|---|---|
| **SUT-error** | The web service misbehaves: wrong status code, schema violation, 5xx, crash, timeout handling | `POST /api/ocr` with a valid image returns 500; response missing `boxes` | app code |
| **Model-error** | The service is correct but Tesseract misses the gate: CER above threshold, metamorphic relation violated, invariant broken | clean receipt CER 0.071 ≥ 0.05; noise monotonicity violated | engine/preprocessing decision (logged) |
| **Data-error** | Ground truth vs image mismatch: the label itself is wrong for the real image | GT address line differs from what is visibly on the receipt | label correction with recorded reason (never "fix" the test) |
| **Test-flake** | Non-deterministic environment failure, not reproducible on rerun: port in use, transient network, browser crash | second run of the identical test passes | environment/CI config |

## Classification procedure

1. Reproduce on the same machine + same commit (if it doesn't reproduce → suspect
   Test-flake; rerun twice before classifying).
2. Is the HTTP layer correct? (status, schema, headers) → if not: **SUT-error**.
3. Is the GT correct? Compare GT fields against the actual image content → if the
   label is wrong: **Data-error** (fix label, record reason in this doc's log below).
4. Otherwise it is a real model miss → **Model-error**; the failure gallery entry
   (input | degraded | GT | pred | defect class) is the artifact of record.

## Log

- _no data-error label corrections recorded yet (2026-09-14)._
