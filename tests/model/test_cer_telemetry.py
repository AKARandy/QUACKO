"""CER telemetry (Option C architecture, user order 2026-09-14).

Absolute accuracy (field-CER, clean + blur + all variants) is MEASURED AND
REPORTED, not gated: these tests assert measurement integrity only (20/20
receipts measured, every CER in [0,1], all texts present). A failure here
means the measurement pipeline or the data is broken (DATA-ERR class) — it
is never a statement about engine accuracy. Values land in
report/cer-run.json -> metrics.json last_run -> dashboard.
"""
import json
import os

from conftest import ROOT
from provenance import get_provenance, now_iso

VARIANTS = ("clean", "blur", "rot", "noise_l", "noise_h", "up2")


def test_cer_all_20_measured_and_in_range(ocr_all):
    recs = ocr_all["receipts"]
    assert len(recs) == 20, f"expected 20 measured receipts, got {len(recs)}"
    for rec in recs:
        for v in VARIANTS:
            assert isinstance(rec[v]["text"], str) and rec[v]["text"] is not None
            assert 0.0 <= rec[v]["cer"] <= 1.0, (
                f"{rec['file']} {v}: CER {rec[v]['cer']} outside [0,1]"
            )
        assert 0.0 <= rec["rot_vs_clean"] <= 1.0

    out = os.path.join(ROOT, "report", "cer-run.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = []
    for rec in recs:
        rows.append(
            {
                "file": rec["file"],
                "conf": rec["conf"],
                "cer_clean": round(rec["clean"]["cer"], 4),
                "cer_blur": round(rec["blur"]["cer"], 4),
                "cer_rot": round(rec["rot"]["cer"], 4),
                "cer_noise_l": round(rec["noise_l"]["cer"], 4),
                "cer_noise_h": round(rec["noise_h"]["cer"], 4),
                "cer_up2": round(rec["up2"]["cer"], 4),
            }
        )
    data = {
        "provenance": get_provenance(),
        "generated": now_iso(),
        "receipts": len(rows),
        "avg_ocr_s": ocr_all["avg_ocr_s"],
        "clean_cer_mean": round(sum(r["cer_clean"] for r in rows) / len(rows), 4),
        "blur_cer_mean": round(sum(r["cer_blur"] for r in rows) / len(rows), 4),
        "m2_sums": {
            "noise_l": round(sum(r["cer_noise_l"] for r in rows), 4),
            "noise_h": round(sum(r["cer_noise_h"] for r in rows), 4),
        },
        "by_receipt": rows,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
