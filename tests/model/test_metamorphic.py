"""MQ-M1..M3 metamorphic oracles (HARD GATE) — behavioral stability.

Tolerances locked 2026-09-14 by explicit user order (Option C
architecture): M1 <= 0.20 (measured worst 0.1454, local Windows /
Tesseract 5.5.0 run 2026-09-14), M3 <= +0.10 (measured worst +0.0583),
M2 = strict AGGREGATE monotonicity (measured sum_light 6.389 <=
sum_heavy 11.2355). Rationale, basis and change procedure:
docs/quality-gates.md. Change only via a new logged user order.
"""
import re

from cer import field_cer
from conftest import set_gallery_ctx

M1_BOUND = 0.20
M3_TOL = 0.10


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def test_mq_m1_rotation_stability(ocr_all):
    bad = []
    for rec in ocr_all["receipts"]:
        r0, r1 = rec["clean"]["text"], rec["rot"]["text"]
        if _norm(r0) == _norm(r1):
            continue
        cer = field_cer(r0, r1)[0]
        if cer > M1_BOUND:
            from degrade import to_array, from_array, rotate3

            set_gallery_ctx(
                file=rec["file"],
                input_bytes=rec["bytes"],
                degraded_bytes=from_array(rotate3(to_array(rec["bytes"]))),
                gt=r0,
                pred=r1,
                cer=round(cer, 4),
                assertion=f"MQ-M1 rotation stability (3 deg): field-CER {cer:.4f} > {M1_BOUND}",
                defect_class="model-error",
            )
            bad.append(f"{rec['file']}: rotated field-CER {cer:.4f} > {M1_BOUND} bound")
    assert not bad, "MQ-M1 violations:\n" + "\n".join(bad)


def test_mq_m2_noise_monotonicity_aggregate(ocr_all):
    recs = ocr_all["receipts"]
    sum_l = sum(r["noise_l"]["cer"] for r in recs)
    sum_h = sum(r["noise_h"]["cer"] for r in recs)
    if sum_h >= sum_l:
        return
    dec = [r for r in recs if r["noise_h"]["cer"] < r["noise_l"]["cer"]]
    for r in dec:
        from degrade import to_array, from_array, noise_sp

        set_gallery_ctx(
            file=r["file"],
            input_bytes=r["bytes"],
            degraded_bytes=from_array(noise_sp(to_array(r["bytes"]), 0.15)),
            gt=r["gt"],
            pred=r["noise_h"]["text"],
            cer=round(r["noise_h"]["cer"], 4),
            assertion=(
                "MQ-M2 aggregate monotonicity violated; per-receipt decrease "
                f"{r['noise_l']['cer']:.4f} -> {r['noise_h']['cer']:.4f}"
            ),
            defect_class="model-error",
        )
    assert False, (
        f"MQ-M2 aggregate: sum_heavy {sum_h:.4f} < sum_light {sum_l:.4f}; per-receipt "
        "decreases (advisory, also in telemetry): "
        + str([(r["file"], round(r["noise_l"]["cer"] - r["noise_h"]["cer"], 4)) for r in dec])
    )


def test_mq_m3_scale_stability(ocr_all):
    bad = []
    for rec in ocr_all["receipts"]:
        c0, c2 = rec["clean"]["cer"], rec["up2"]["cer"]
        if c2 > c0 + M3_TOL:
            from degrade import to_array, from_array, upscale2

            set_gallery_ctx(
                file=rec["file"],
                input_bytes=rec["bytes"],
                degraded_bytes=from_array(upscale2(to_array(rec["bytes"]))),
                gt=rec["gt"],
                pred=rec["up2"]["text"],
                cer=round(c2, 4),
                assertion=f"MQ-M3 scale stability (2x upscale degraded CER {c0:.4f} -> {c2:.4f})",
                defect_class="model-error",
            )
            bad.append(f"{rec['file']}: 2x upscale degraded CER {c0:.4f} -> {c2:.4f} (> +{M3_TOL})")
    assert not bad, "MQ-M3 violations:\n" + "\n".join(bad)
