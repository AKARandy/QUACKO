"""API contract + performance tests (PLAN-V2 §3.3). Real SUT subprocess, real golden data."""
import io
import json
import os
import time

import requests
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "not-an-image.txt")


def test_api_1_schema(sut, golden):
    item = golden[0]
    r = requests.post(f"{sut}/api/ocr", files={"image": (item["file"], item["bytes"])}, timeout=120)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    assert set(body) == {"text", "confidence", "boxes"}
    assert isinstance(body["text"], str)
    assert isinstance(body["confidence"], float)
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["boxes"], list)
    for b in body["boxes"]:
        assert isinstance(b, list) and len(b) == 4
        assert all(isinstance(v, int) for v in b)


def test_api_2_txt_upload_400(sut):
    with open(FIXTURE, "rb") as fh:
        r = requests.post(f"{sut}/api/ocr", files={"image": ("not-an-image.txt", fh.read())}, timeout=30)
    assert r.status_code == 400


def test_api_3_missing_file_400(sut):
    r = requests.post(f"{sut}/api/ocr", timeout=30)
    assert r.status_code == 400


def test_api_4_oversized_413(sut, golden):
    blob = None
    for item in sorted(golden, key=lambda g: len(g["bytes"]), reverse=True):
        img = Image.open(io.BytesIO(item["bytes"])).convert("RGB")
        for scale in (2, 3, 4, 6, 8):
            big = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
            buf = io.BytesIO()
            big.save(buf, "JPEG", quality=95)
            if buf.tell() > 8 * 1024 * 1024:
                blob = buf.getvalue()
                break
        if blob is not None:
            break
    assert blob is not None, "could not build a >8MiB real JPEG from the golden set"
    assert len(blob) > 8 * 1024 * 1024
    r = requests.post(f"{sut}/api/ocr", files={"image": ("big.jpg", blob)}, timeout=60)
    assert r.status_code == 413


def test_api_5_health(sut):
    t0 = time.perf_counter()
    r = requests.get(f"{sut}/health", timeout=10)
    dt = time.perf_counter() - t0
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "engine": "tesseract"}
    assert dt < 1.0, f"health took {dt:.3f}s"


def test_api_6_latency(sut, golden):
    """API-6: latency is TELEMETRY (Option C order 2026-09-14 — reported, not
    gated). The gate is the API contract itself: all 5 real POSTs must return
    200. Measured values are logged to data/baselines/api-latency.json."""
    item = golden[0]
    runs = []
    statuses = []
    for _ in range(5):
        t0 = time.perf_counter()
        r = requests.post(f"{sut}/api/ocr", files={"image": (item["file"], item["bytes"])}, timeout=120)
        runs.append(time.perf_counter() - t0)
        statuses.append(r.status_code)
    mean = sum(runs) / len(runs)
    out = os.path.join(ROOT, "data", "baselines", "api-latency.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "runs_s": [round(t, 3) for t in runs],
                "mean_s": round(mean, 3),
                "telemetry": True,
                "note": "reported metric, not a gate (Option C order 2026-09-14)",
                "basis": f"5 real POSTs on {item['file']} via local Flask subprocess",
            },
            fh,
            indent=2,
        )
    assert all(s == 200 for s in statuses), f"API contract violated: statuses {statuses}"


def test_api_7_boxes_in_bounds(sut, golden):
    for item in golden[:5]:
        img = Image.open(io.BytesIO(item["bytes"]))
        W, H = img.size
        r = requests.post(f"{sut}/api/ocr", files={"image": (item["file"], item["bytes"])}, timeout=120)
        assert r.status_code == 200
        for (x, y, w, h) in r.json()["boxes"]:
            assert 0 <= x and 0 <= y and x + w <= W and y + h <= H, (
                f"{item['file']}: box {x},{y},{w},{h} outside {W}x{H}"
            )
