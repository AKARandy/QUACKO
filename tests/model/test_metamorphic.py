"""MQ-M1..M3 metamorphic oracles (PLAN-V2 §3.2) — relations on real inputs."""
import re

from ocr_engine import ocr_bytes
from cer import field_cer
from degrade import to_array, from_array, rotate3, noise_sp, upscale2
from conftest import set_gallery_ctx


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def test_mq_m1_rotation_invariance(golden):
    bad = []
    for item in golden:
        img = to_array(item["bytes"])
        rot = rotate3(img)
        r0 = ocr_bytes(item["bytes"])["text"]
        r1 = ocr_bytes(from_array(rot))["text"]
        if _norm(r0) != _norm(r1):
            cer = field_cer(r0, r1)[0]
            if cer > 0.05:
                set_gallery_ctx(
                    file=item["file"],
                    input_bytes=item["bytes"],
                    degraded_bytes=from_array(rot),
                    gt=r0,
                    pred=r1,
                    cer=round(cer, 4),
                    assertion="MQ-M1 rotation invariance (3 deg)",
                    defect_class="model-error",
                )
                bad.append(f"{item['file']}: rotated field-CER {cer:.4f} > 0.05 fallback bound")
    assert not bad, "MQ-M1 violations:\n" + "\n".join(bad)


def test_mq_m2_noise_monotonicity(golden):
    bad = []
    for item in golden:
        img = to_array(item["bytes"])
        light = ocr_bytes(from_array(noise_sp(img, 0.02)))["text"]
        heavy = ocr_bytes(from_array(noise_sp(img, 0.15)))["text"]
        cer_l = field_cer(item["gt"], light)[0]
        cer_h = field_cer(item["gt"], heavy)[0]
        if cer_h < cer_l:
            set_gallery_ctx(
                file=item["file"],
                input_bytes=item["bytes"],
                degraded_bytes=from_array(noise_sp(img, 0.15)),
                gt=item["gt"],
                pred=heavy,
                cer=round(cer_h, 4),
                assertion=f"MQ-M2 noise monotonicity (CER must not decrease: light={cer_l:.4f} > heavy={cer_h:.4f})",
                defect_class="model-error",
            )
            bad.append(f"{item['file']}: CER decreased under more noise (light {cer_l:.4f} -> heavy {cer_h:.4f})")
    assert not bad, "MQ-M2 violations:\n" + "\n".join(bad)


def test_mq_m3_scale_invariance(golden):
    bad = []
    for item in golden:
        img = to_array(item["bytes"])
        r0 = ocr_bytes(item["bytes"])["text"]
        r2 = ocr_bytes(from_array(upscale2(img)))["text"]
        cer0 = field_cer(item["gt"], r0)[0]
        cer2 = field_cer(item["gt"], r2)[0]
        if cer2 > cer0 + 0.01:
            set_gallery_ctx(
                file=item["file"],
                input_bytes=item["bytes"],
                degraded_bytes=from_array(upscale2(img)),
                gt=item["gt"],
                pred=r2,
                cer=round(cer2, 4),
                assertion=f"MQ-M3 scale invariance (2x upscale degraded CER {cer0:.4f} -> {cer2:.4f})",
                defect_class="model-error",
            )
            bad.append(f"{item['file']}: 2x upscale degraded CER {cer0:.4f} -> {cer2:.4f} (> +0.01)")
    assert not bad, "MQ-M3 violations:\n" + "\n".join(bad)
