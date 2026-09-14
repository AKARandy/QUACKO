"""Thin pytesseract wrapper over system Tesseract 5.

Real engine only â€” no stub / fake / mock fallback. Missing engine or
unidentified input raises; callers surface the error (fail fast, NO-LARP).

Pipeline (calibrated 2026-09-14 on the Committed 20, see
docs/quality-gates.md): grayscale -> max-side normalization into
[1600, 2400] px -> gated deskew (median Hough line angle, applied only
with >= 8 lines, |angle| >= 0.3 deg, angle IQR <= 5 deg) -> Tesseract
PSM 6. Returned boxes are mapped back to original image coordinates.
"""
import io

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
import pytesseract

MIN_SIDE = 1600
MAX_SIDE = 2400
PSM = 6
DESKEW_MIN_ANGLE = 0.3
DESKEW_MIN_LINES = 8
DESKEW_MAX_IQR = 5.0

# QA SUT: uploads are size-capped (8 MiB) and every image is normalized to
# <= 2400 px max side; PIL's decompression-bomb limit would false-positive
# on large legitimate scans (e.g. 5900 px receipts upsampled by test fixtures).
Image.MAX_IMAGE_PIXELS = None


def _working(img):
    gray = img.convert("L")
    w, h = gray.size
    m = max(w, h)
    scale = 1.0
    if m < MIN_SIDE:
        scale = MIN_SIDE / m
    elif m > MAX_SIDE:
        scale = MAX_SIDE / m
    if scale != 1.0:
        gray = gray.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return gray, scale


def _estimate_skew(arr):
    edges = cv2.Canny(arr, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=200, minLineLength=arr.shape[1] // 4, maxLineGap=20
    )
    if lines is None:
        return 0.0, 0, 0.0
    angles = []
    for l in lines:
        x1, y1, x2, y2 = np.asarray(l).ravel()[:4]
        a = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(a) < 15:
            angles.append(a)
    if len(angles) < 2:
        return 0.0, len(angles), 0.0
    med = float(np.median(angles))
    iqr = float(np.percentile(angles, 75) - np.percentile(angles, 25))
    return med, len(angles), iqr


def _deskew(arr):
    med, n, iqr = _estimate_skew(arr)
    if n < DESKEW_MIN_LINES or abs(med) < DESKEW_MIN_ANGLE or iqr > DESKEW_MAX_IQR:
        return arr
    h, w = arr.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), med, 1.0)
    return cv2.warpAffine(arr, m, (w, h), borderValue=255, flags=cv2.INTER_LINEAR)


def ocr_bytes(data: bytes) -> dict:
    """Run real Tesseract OCR on raw image bytes.

    Returns {"text": str, "confidence": float 0..1, "boxes": [[x,y,w,h]] in
    original image coords, "width": int, "height": int (original image size)}.
    Raises UnidentifiedImageError on non-images.
    """
    img = Image.open(io.BytesIO(data))
    img.load()
    W, H = img.width, img.height
    big, scale = _working(img)
    arr = _deskew(np.array(big))
    d = pytesseract.image_to_data(
        Image.fromarray(arr), config=f"--psm {PSM}", output_type=pytesseract.Output.DICT
    )
    n = len(d["text"])
    line_map = {}
    boxes = []
    confs = []
    for i in range(n):
        try:
            conf = int(float(d["conf"][i]))
        except (TypeError, ValueError):
            continue
        txt = (d["text"][i] or "").strip()
        if conf < 0 or not txt:
            continue
        confs.append(conf)
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        line_map.setdefault(key, []).append(txt)
        x = max(0, min(W - 1, int(d["left"][i] / scale)))
        y = max(0, min(H - 1, int(d["top"][i] / scale)))
        bw = max(1, min(W - x, int(d["width"][i] / scale)))
        bh = max(1, min(H - y, int(d["height"][i] / scale)))
        boxes.append([x, y, bw, bh])
    text = "\n".join(" ".join(v) for v in line_map.values())
    confidence = round(sum(confs) / len(confs) / 100.0, 4) if confs else 0.0
    return {
        "text": text,
        "confidence": confidence,
        "boxes": boxes,
        "width": W,
        "height": H,
    }
