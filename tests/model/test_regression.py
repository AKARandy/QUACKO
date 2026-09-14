"""REG-1/REG-2 regression gate (HARD GATE, Option C, user order 2026-09-14).

Per-receipt CER (clean, blur) must not degrade by more than 10% relative to
the committed baseline (data/baselines/metrics.json, `baseline` section):
    run_cer <= max(0.01, 1.10 x baseline_cer)
The 0.01 absolute floor is a labeled judgment parameter: it covers receipts
whose baseline CER is exactly 0.0, where '10% of zero' is unusable.

Provenance-aware (addendum 2026-09-14): if the current run's OS / Tesseract
version / pipeline differs from the baseline's provenance, violations are
reported as an ENVIRONMENT DELTA — the documented fix is a re-baseline from
CI artifacts under a logged order (docs/quality-gates.md), not a gate edit.
Environment-delta violations are NOT captured in the failure gallery (the
gallery is for genuine model misses); the baseline section is never touched
by a run.
"""
import json
import os

from conftest import ROOT, set_gallery_ctx
from provenance import get_provenance

REL = 1.10
FLOOR = 0.01
BASELINE_PATH = os.path.join(ROOT, "data", "baselines", "metrics.json")


def _baseline():
    if not os.path.exists(BASELINE_PATH):
        raise RuntimeError(
            "DATA-ERR: data/baselines/metrics.json missing — re-baseline "
            "(scripts/calibrate.py + logged order) before running the regression gate"
        )
    with open(BASELINE_PATH, encoding="utf-8") as fh:
        m = json.load(fh)
    base = m.get("baseline")
    if not base:
        raise RuntimeError("DATA-ERR: metrics.json has no `baseline` section (schema 2 required)")
    return base


def _env_delta(base_prov: dict):
    cur = get_provenance()
    diffs = [k for k in ("tesseract_version", "os_family", "pipeline") if cur.get(k) != base_prov.get(k)]
    return diffs, cur


def _check(kind: str, ocr_all):
    base = _baseline()
    base_by = {r["file"]: r[f"cer_{kind}"] for r in base["by_receipt"]}
    diffs, cur = _env_delta(base["provenance"])
    delta = bool(diffs)
    bad = []
    for rec in ocr_all["receipts"]:
        b = base_by.get(rec["file"])
        if b is None:
            raise RuntimeError(f"DATA-ERR: {rec['file']} missing from baseline by_receipt")
        limit = max(FLOOR, REL * b)
        c = rec[kind]["cer"]
        if c > limit:
            msg = (
                f"{rec['file']}: {kind} CER {c:.4f} > {limit:.4f} "
                f"(baseline {b:.4f}; rule: max(0.01, 1.10 x baseline))"
            )
            if delta:
                msg += (
                    f" [ENVIRONMENT DELTA: baseline {base['provenance']['os_family']}/"
                    f"Tesseract {base['provenance']['tesseract_version']} vs current "
                    f"{cur['os_family']}/Tesseract {cur['tesseract_version']}; "
                    f"differs in {diffs} — re-baseline per docs/quality-gates.md]"
                )
            else:
                set_gallery_ctx(
                    file=rec["file"],
                    input_bytes=rec["bytes"],
                    gt=rec["gt"],
                    pred=rec[kind]["text"],
                    cer=round(c, 4),
                    assertion=f"REG-{kind.upper()}: CER {c:.4f} > baseline {b:.4f} + 10%",
                    defect_class="model-error",
                )
            bad.append(msg)
    assert not bad, f"REG-{kind.upper()} violations:\n" + "\n".join(bad)


def test_reg_1_clean(ocr_all):
    _check("clean", ocr_all)


def test_reg_2_blur(ocr_all):
    _check("blur", ocr_all)
