"""Shared fixtures: the Committed 20 (SHA256-verified, fail fast) + a real
SUT subprocess. No stubs, no synthetic inputs, no downloads at test time."""
import hashlib
import json
import os
import subprocess
import sys
import time

import pytest
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "app"), os.path.join(ROOT, "tests"), os.path.join(ROOT, "tests", "model")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GOLDEN = os.path.join(ROOT, "data", "golden")
PORT = 5000
BASE = f"http://127.0.0.1:{PORT}"

# The failure gallery must reflect the CURRENT run only: clear stale captures
# from earlier runs at collection time (CI is a fresh checkout; local
# accumulates). capture_failure() recreates the dir on demand.
import shutil  # noqa: E402

shutil.rmtree(os.path.join(ROOT, "report", "failures"), ignore_errors=True)

from gallery import set_gallery_ctx  # noqa: E402,F401  (re-exported for tests)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_golden():
    """Load the 20 pinned real receipts + labels; verify every SHA256.
    Missing file or hash mismatch => hard error (DATA-ERR), never substitute."""
    man_path = os.path.join(GOLDEN, "MANIFEST-20.sha256")
    labels_path = os.path.join(GOLDEN, "labels.json")
    if not (os.path.exists(man_path) and os.path.exists(labels_path)):
        raise RuntimeError(
            "DATA-ERR: data/golden missing MANIFEST-20.sha256 or labels.json — "
            "run scripts/fetch_golden20.py first"
        )
    pins = {}
    with open(man_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                digest, name = line.split()
                pins[name] = digest
    with open(labels_path, encoding="utf-8") as fh:
        labels = json.load(fh)
    if set(pins) != set(labels):
        raise RuntimeError(f"DATA-ERR: manifest/labels mismatch: {sorted(set(pins) ^ set(labels))}")
    items = []
    for name in sorted(pins):
        path = os.path.join(GOLDEN, name)
        if not os.path.exists(path):
            raise RuntimeError(f"DATA-ERR: missing golden file {name}")
        actual = _sha256(path)
        if actual != pins[name]:
            raise RuntimeError(
                f"DATA-ERR: SHA256 mismatch for {name}: pinned {pins[name]}, got {actual}"
            )
        with open(path, "rb") as fh:
            items.append({"file": name, "gt": labels[name], "bytes": fh.read(), "path": path})
    if len(items) != 20:
        raise RuntimeError(f"DATA-ERR: expected 20 golden images, found {len(items)}")
    return items


@pytest.fixture(scope="session")
def golden():
    return load_golden()


@pytest.fixture(scope="session")
def sut(golden):  # depends on golden: fail fast on data before starting the server
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "app", "main.py")],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    up = False
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            if requests.get(f"{BASE}/health", timeout=2).status_code == 200:
                up = True
                break
        except requests.ConnectionError:
            time.sleep(0.5)
    if not up:
        proc.terminate()
        raise RuntimeError("DATA-ERR: SUT /health did not come up within 60 s")
    yield BASE
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def ocr_all(golden):
    """Real engine OCR of all 20 receipts x 6 variants, once per session.
    Shared by invariant / metamorphic / telemetry / regression tests so each
    image is measured exactly once per run (deterministic engine)."""
    from cer import field_cer
    from degrade import to_array, from_array, blur_heavy, noise_sp, rotate3, upscale2
    from ocr_engine import ocr_bytes

    receipts = []
    t_sum = 0.0
    n = 0
    for item in golden:
        t0 = time.perf_counter()
        r = ocr_bytes(item["bytes"])
        t_sum += time.perf_counter() - t0
        n += 1
        rec = {
            "file": item["file"],
            "gt": item["gt"],
            "bytes": item["bytes"],
            "conf": r["confidence"],
            "width": r["width"],
            "height": r["height"],
            "boxes": r["boxes"],
            "clean": {"text": r["text"], "cer": field_cer(item["gt"], r["text"])[0]},
        }
        img = to_array(item["bytes"])
        for name, variant in (
            ("blur", blur_heavy(img)),
            ("rot", rotate3(img)),
            ("noise_l", noise_sp(img, 0.02)),
            ("noise_h", noise_sp(img, 0.15)),
            ("up2", upscale2(img)),
        ):
            t0 = time.perf_counter()
            rv = ocr_bytes(from_array(variant))
            t_sum += time.perf_counter() - t0
            n += 1
            rec[name] = {"text": rv["text"], "cer": field_cer(item["gt"], rv["text"])[0]}
        rec["rot_vs_clean"] = field_cer(r["text"], rec["rot"]["text"])[0]
        receipts.append(rec)
    return {"receipts": receipts, "avg_ocr_s": round(t_sum / n, 3)}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture a real model-quality failure into the gallery (never crashes the run)."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        try:
            rel = os.path.relpath(str(item.path), ROOT).replace(os.sep, "/")
            if rel.startswith("tests/model/"):
                from gallery import capture_failure

                capture_failure(item)
        except Exception as exc:  # noqa: BLE001
            print(f"gallery: hook error: {exc}")
