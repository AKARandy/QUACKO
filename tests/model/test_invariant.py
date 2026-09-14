"""MQ-I1..I3 invariant oracles (PLAN-V2 §3.2) — must hold on every call."""
import pytest

from ocr_engine import ocr_bytes


@pytest.fixture(scope="module")
def all_ocr(golden):
    out = {}
    for item in golden:
        out[item["file"]] = (item, ocr_bytes(item["bytes"]))
    return out


def test_mq_i1_confidence_bounds(all_ocr):
    for f, (item, r) in all_ocr.items():
        assert 0.0 <= r["confidence"] <= 1.0, f"{f}: confidence {r['confidence']} outside [0,1]"


def test_mq_i2_boxes_in_bounds(all_ocr):
    for f, (item, r) in all_ocr.items():
        W, H = r["width"], r["height"]
        for (x, y, w, h) in r["boxes"]:
            assert 0 <= x and 0 <= y and x + w <= W and y + h <= H, (
                f"{f}: box {x},{y},{w},{h} outside image {W}x{H}"
            )


def test_mq_i3_nonempty_text(all_ocr):
    for f, (item, r) in all_ocr.items():
        assert r["text"].strip(), f"{f}: empty text on text-bearing receipt"
