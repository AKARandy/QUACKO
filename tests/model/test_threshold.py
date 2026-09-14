"""MQ-T1/T2 threshold oracles — field-anchored CER (PLAN-V2 §3.2).
Gates provisional until the Phase-2 calibration log in docs/quality-gates.md."""
from ocr_engine import ocr_bytes
from cer import field_cer
from degrade import to_array, from_array, blur_heavy
from conftest import set_gallery_ctx

GATE_CLEAN = 0.05
GATE_BLUR = 0.25


def test_mq_t1_clean_cer_under_gate(golden):
    fails = []
    for item in golden:
        r = ocr_bytes(item["bytes"])
        cer, detail = field_cer(item["gt"], r["text"])
        if cer >= GATE_CLEAN:
            set_gallery_ctx(
                file=item["file"],
                input_bytes=item["bytes"],
                gt=item["gt"],
                pred=r["text"],
                cer=round(cer, 4),
                assertion="MQ-T1 clean CER < 0.05",
                defect_class="model-error",
            )
            fails.append(
                f"{item['file']}: clean CER {cer:.4f} >= {GATE_CLEAN} "
                f"(per-field: {[(f, round(c, 3)) for f, c in detail]})"
            )
    assert not fails, "MQ-T1 gate misses:\n" + "\n".join(fails)


def test_mq_t2_heavy_blur_cer_under_gate(golden):
    fails = []
    for item in golden:
        img = to_array(item["bytes"])
        r = ocr_bytes(from_array(blur_heavy(img)))
        cer, detail = field_cer(item["gt"], r["text"])
        if cer >= GATE_BLUR:
            set_gallery_ctx(
                file=item["file"],
                input_bytes=item["bytes"],
                degraded_bytes=from_array(blur_heavy(img)),
                gt=item["gt"],
                pred=r["text"],
                cer=round(cer, 4),
                assertion="MQ-T2 blur CER < 0.25",
                defect_class="model-error",
            )
            fails.append(f"{item['file']}: blur CER {cer:.4f} >= {GATE_BLUR}")
    assert not fails, "MQ-T2 gate misses:\n" + "\n".join(fails)
