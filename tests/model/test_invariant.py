"""MQ-I1..I3 invariant oracles (HARD GATE) — must hold on every real call."""


def test_mq_i1_confidence_bounds(ocr_all):
    for rec in ocr_all["receipts"]:
        assert 0.0 <= rec["conf"] <= 1.0, f"{rec['file']}: confidence {rec['conf']} outside [0,1]"


def test_mq_i2_boxes_in_bounds(ocr_all):
    for rec in ocr_all["receipts"]:
        W, H = rec["width"], rec["height"]
        for (x, y, w, h) in rec["boxes"]:
            assert 0 <= x and 0 <= y and x + w <= W and y + h <= H, (
                f"{rec['file']}: box {x},{y},{w},{h} outside image {W}x{H}"
            )


def test_mq_i3_nonempty_text(ocr_all):
    for rec in ocr_all["receipts"]:
        assert rec["clean"]["text"].strip(), f"{rec['file']}: empty text on text-bearing receipt"
