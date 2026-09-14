"""Failure-gallery capture (PLAN-V2 §5). Real failures only; never crashes a run."""
import io
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX: dict = {}
_counter = {"n": 0}


def set_gallery_ctx(**kw):
    CTX.clear()
    CTX.update(kw)


def capture_failure(item):
    try:
        if not CTX:
            return
        _counter["n"] += 1
        slug = f"{_counter['n']:02d}-{str(item.name).replace('test_', '')}-{CTX.get('file', 'x')}"
        d = os.path.join(ROOT, "report", "failures", slug)
        os.makedirs(d, exist_ok=True)
        for key, fn in (("input_bytes", "input.png"), ("degraded_bytes", "degraded.png")):
            if CTX.get(key):
                try:
                    Image.open(io.BytesIO(CTX[key])).save(os.path.join(d, fn))
                except Exception:  # noqa: BLE001 — capture best-effort
                    pass
        with open(os.path.join(d, "gt.txt"), "w", encoding="utf-8") as fh:
            fh.write(str(CTX.get("gt", "")))
        with open(os.path.join(d, "pred.txt"), "w", encoding="utf-8") as fh:
            fh.write(str(CTX.get("pred", "")))
        with open(os.path.join(d, "metrics.json"), "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "assertion": str(CTX.get("assertion", "")),
                    "cer": CTX.get("cer"),
                    "defect_class": str(CTX.get("defect_class", "model-error")),
                    "test": item.nodeid,
                },
                fh,
                indent=2,
            )
        with open(os.path.join(d, "defect-class.txt"), "w", encoding="utf-8") as fh:
            fh.write(str(CTX.get("defect_class", "model-error")))
    except Exception as exc:  # noqa: BLE001
        print(f"gallery: capture failed: {exc}")
