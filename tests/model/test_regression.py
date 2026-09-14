"""REG-1/REG-2 regression gate (HARD GATE, Option C, user order 2026-09-14;
multi-baseline selection per user order 2026-09-14).

Per-receipt CER (clean, blur) must not degrade by more than 10% relative to
the SELECTED baseline — the entry in data/baselines/metrics.json `baselines`
whose provenance (os_family + tesseract_version) matches the running
environment:
    run_cer <= max(0.01, 1.10 x baseline_cer)
The 0.01 absolute floor is a labeled judgment parameter: it covers receipts
whose baseline CER is exactly 0.0, where '10% of zero' is unusable.

Fail-closed (addendum 2026-09-14): if no baseline entry matches the current
provenance, the gate FAILS with an explicit ENV-DELTA error naming the
mismatch — never a silent cross-environment comparison. The fix is a logged
re-baseline (scripts/add_baseline.py from CI artifacts, or
scripts/calibrate.py), never a gate edit. The `baselines` list is never
touched by a run.
"""
import json
import os

from conftest import ROOT, set_gallery_ctx
from provenance import get_provenance

REL = 1.10
FLOOR = 0.01
BASELINE_PATH = os.path.join(ROOT, "data", "baselines", "metrics.json")


def _entries():
    if not os.path.exists(BASELINE_PATH):
        raise RuntimeError(
            "DATA-ERR: data/baselines/metrics.json missing — re-baseline "
            "(scripts/calibrate.py + logged order) before running the regression gate"
        )
    with open(BASELINE_PATH, encoding="utf-8") as fh:
        m = json.load(fh)
    if isinstance(m.get("baselines"), list) and m["baselines"]:
        return m["baselines"]
    if isinstance(m.get("baseline"), dict):  # legacy schema 2, single entry
        return [dict(m["baseline"], id=1)]
    raise RuntimeError("DATA-ERR: metrics.json has no `baselines` list (schema 3 required)")


def _select_baseline():
    """Return the baseline entry matching this environment, or fail closed."""
    entries = _entries()
    cur = get_provenance()
    hits = [
        b for b in entries
        if b.get("provenance", {}).get("os_family") == cur.get("os_family")
        and b.get("provenance", {}).get("tesseract_version") == cur.get("tesseract_version")
    ]
    if len(hits) == 1:
        return hits[0]
    known = [f"#{b.get('id')}: {b.get('provenance', {}).get('os_family')}/"
             f"Tesseract {b.get('provenance', {}).get('tesseract_version')}" for b in entries]
    assert False, (
        "REG ENV-DELTA (fail closed): no baseline matches current provenance "
        f"{cur.get('os_family')}/Tesseract {cur.get('tesseract_version')} "
        f"({len(hits)} matches; known baselines: {'; '.join(known)}). "
        "Add one via scripts/add_baseline.py from a real run record under a "
        "logged order (docs/quality-gates.md) — never compare cross-environment."
    )


def _check(kind: str, ocr_all):
    base = _select_baseline()
    base_by = {r["file"]: r[f"cer_{kind}"] for r in base["by_receipt"]}
    bad = []
    for rec in ocr_all["receipts"]:
        b = base_by.get(rec["file"])
        if b is None:
            raise RuntimeError(f"DATA-ERR: {rec['file']} missing from baseline #{base.get('id')} by_receipt")
        limit = max(FLOOR, REL * b)
        c = rec[kind]["cer"]
        if c > limit:
            set_gallery_ctx(
                file=rec["file"],
                input_bytes=rec["bytes"],
                gt=rec["gt"],
                pred=rec[kind]["text"],
                cer=round(c, 4),
                assertion=f"REG-{kind.upper()} (baseline #{base.get('id')}): CER {c:.4f} > baseline {b:.4f} + 10%",
                defect_class="model-error",
            )
            bad.append(
                f"{rec['file']}: {kind} CER {c:.4f} > {limit:.4f} "
                f"(baseline #{base.get('id')} {b:.4f}; rule: max(0.01, 1.10 x baseline))"
            )
    assert not bad, f"REG-{kind.upper()} violations:\n" + "\n".join(bad)


def test_reg_1_clean(ocr_all):
    _check("clean", ocr_all)


def test_reg_2_blur(ocr_all):
    _check("blur", ocr_all)
