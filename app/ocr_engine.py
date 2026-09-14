"""Thin pytesseract wrapper over system Tesseract 5.

Real engine only — no stub / fake / mock fallback. Missing engine or
unidentified input raises; callers surface the error (fail fast, NO-LARP).

Working size: grayscale; max side normalized into [1600, 2400] px (upscale
small scans, downscale huge scans). Returned boxes are mapped back to the
original image coordinates.
"""
import io

from PIL import Image, UnidentifiedImageError
import pytesseract

MIN_SIDE = 1600
MAX_SIDE = 2400


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
    d = pytesseract.image_to_data(big, output_type=pytesseract.Output.DICT)
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
