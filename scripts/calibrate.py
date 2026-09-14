"""Re-baseline act (Option C architecture, user order 2026-09-14).

Measures all six variants (clean, heavy blur, 3-deg rotation, 2% / 15% salt &
pepper, 2x upscale) on the Committed 20 with the real engine and writes the
`baseline` section of data/baselines/metrics.json (schema 2: baseline +
last_run). Provenance (OS + Tesseract version + pipeline) is recorded so an
environment delta is diagnosable (docs/quality-gates.md, re-baseline
procedure).

This script is the ONLY writer of the `baseline` section. Running it +
committing the result is a logged re-baseline act — never run silently.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "app"), os.path.join(ROOT, "tests"), os.path.join(ROOT, "tests", "model")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from conftest import load_golden  # noqa: E402
from cer import field_cer  # noqa: E402
from degrade import to_array, from_array, blur_heavy, noise_sp, rotate3, upscale2  # noqa: E402
from ocr_engine import ocr_bytes  # noqa: E402
from provenance import get_provenance, now_iso  # noqa: E402

OUT = os.path.join(ROOT, "data", "baselines", "metrics.json")
VARIANTS = (
    ("blur", blur_heavy),
    ("rot", rotate3),
    ("noise_l", lambda img: noise_sp(img, 0.02)),
    ("noise_h", lambda img: noise_sp(img, 0.15)),
    ("up2", upscale2),
)


def main():
    golden = load_golden()
    rows = []
    t_sum = 0.0
    n_ocr = 0
    for item in golden:
        t0 = time.perf_counter()
        r = ocr_bytes(item["bytes"])
        t_sum += time.perf_counter() - t0
        n_ocr += 1
        row = {
            "file": item["file"],
            "conf": r["confidence"],
            "cer_clean": round(field_cer(item["gt"], r["text"])[0], 4),
        }
        img = to_array(item["bytes"])
        for name, fn in VARIANTS:
            t0 = time.perf_counter()
            rv = ocr_bytes(from_array(fn(img)))
            t_sum += time.perf_counter() - t0
            n_ocr += 1
            row[f"cer_{name}"] = round(field_cer(item["gt"], rv["text"])[0], 4)
        rows.append(row)
        print(
            f"{item['file']}  clean={row['cer_clean']:.4f} blur={row['cer_blur']:.4f} "
            f"rot={row['cer_rot']:.4f} n2={row['cer_noise_l']:.4f} n15={row['cer_noise_h']:.4f} "
            f"up2={row['cer_up2']:.4f} conf={row['conf']:.3f}"
        )

    clean = [r["cer_clean"] for r in rows]
    blur = [r["cer_blur"] for r in rows]
    sum_l = sum(r["cer_noise_l"] for r in rows)
    sum_h = sum(r["cer_noise_h"] for r in rows)
    metrics = {
        "schema": 2,
        "baseline": {
            "provenance": get_provenance(),
            "generated": now_iso(),
            "receipts": len(rows),
            "clean_cer_mean": round(sum(clean) / len(clean), 4),
            "blur_cer_mean": round(sum(blur) / len(blur), 4),
            "m2_sums": {"noise_l": round(sum_l, 4), "noise_h": round(sum_h, 4)},
            "avg_ocr_s": round(t_sum / n_ocr, 3),
            "by_receipt": rows,
        },
        "last_run": None,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    print()
    print(f"mean clean CER = {metrics['baseline']['clean_cer_mean']:.4f}")
    print(f"mean blur  CER = {metrics['baseline']['blur_cer_mean']:.4f}")
    print(f"M2 aggregate   = sum_light {sum_l:.4f} -> sum_heavy {sum_h:.4f} "
          f"({'monotonic: OK' if sum_h >= sum_l else 'VIOLATION'})")
    print(f"avg OCR time   = {metrics['baseline']['avg_ocr_s']} s over {n_ocr} OCR calls")
    print(f"provenance     = {metrics['baseline']['provenance']}")
    print(f"wrote {OUT} (baseline section; last_run reset to null)")


if __name__ == "__main__":
    main()
