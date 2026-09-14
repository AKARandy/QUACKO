"""Re-baseline act (Option C architecture, user order 2026-09-14;
multi-baseline selection per user order 2026-09-14).

Measures all six variants (clean, heavy blur, 3-deg rotation, 2% / 15% salt &
pepper, 2x upscale) on the Committed 20 with the real engine and adds the
result as an entry in data/baselines/metrics.json `baselines` (schema 3).
Provenance (OS + Tesseract version + pipeline) is recorded; an entry with
the same (os_family, tesseract_version) is replaced, otherwise appended —
other entries (other environments) are never touched.

This script (fresh measurement) and scripts/add_baseline.py (entry from a
logged CI run record) are the ONLY writers of `baselines`. Running either +
committing the result is a logged re-baseline act — never run silently.
For a CI environment, prefer add_baseline.py on the CI artifact over
re-measuring locally.
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
    entry = {
        "provenance": get_provenance(),
        "generated": now_iso(),
        "receipts": len(rows),
        "clean_cer_mean": round(sum(clean) / len(clean), 4),
        "blur_cer_mean": round(sum(blur) / len(blur), 4),
        "m2_sums": {"noise_l": round(sum_l, 4), "noise_h": round(sum_h, 4)},
        "avg_ocr_s": round(t_sum / n_ocr, 3),
        "by_receipt": rows,
    }
    metrics = {"schema": 3, "baselines": [], "last_run": None}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fh:
            old = json.load(fh)
        if isinstance(old.get("baselines"), list):
            metrics["baselines"] = old["baselines"]
        elif isinstance(old.get("baseline"), dict):  # legacy schema 2
            metrics["baselines"] = [dict(old["baseline"], id=1)]
        metrics["last_run"] = old.get("last_run")
    prov = entry["provenance"]
    metrics["baselines"] = [
        e for e in metrics["baselines"]
        if not (e.get("provenance", {}).get("os_family") == prov["os_family"]
                and e.get("provenance", {}).get("tesseract_version") == prov["tesseract_version"])
    ]
    entry["id"] = max([e.get("id", 0) for e in metrics["baselines"]] + [0]) + 1
    metrics["baselines"].append(entry)
    metrics["baselines"].sort(key=lambda e: e.get("id", 0))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    print()
    print(f"baseline #{entry['id']}")
    print(f"mean clean CER = {entry['clean_cer_mean']:.4f}")
    print(f"mean blur  CER = {entry['blur_cer_mean']:.4f}")
    print(f"M2 aggregate   = sum_light {sum_l:.4f} -> sum_heavy {sum_h:.4f} "
          f"({'monotonic: OK' if sum_h >= sum_l else 'VIOLATION'})")
    print(f"avg OCR time   = {entry['avg_ocr_s']} s over {n_ocr} OCR calls")
    print(f"provenance     = {entry['provenance']}")
    print(f"wrote {OUT} (entry #{entry['id']}; other entries + last_run untouched)")


if __name__ == "__main__":
    main()
