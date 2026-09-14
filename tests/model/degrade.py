"""In-memory, seeded degradation of real golden images (PLAN-V2 §3.2).
Derivation of real data only — nothing is generated, nothing is written to disk."""
import cv2
import numpy as np


def to_array(b: bytes):
    nparr = np.frombuffer(b, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("cv2 could not decode image bytes")
    return img


def from_array(img) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("cv2 could not re-encode array")
    return buf.tobytes()


def jpeg_quality(img, q: int):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    if not ok:
        raise ValueError("cv2 jpeg encode failed")
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def blur_heavy(img):
    return cv2.GaussianBlur(img, (5, 5), 2.0)


def noise_sp(img, frac: float, seed: int = 42):
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    n = int(h * w * frac)
    ys = rng.integers(0, h, n)
    xs = rng.integers(0, w, n)
    out = img.copy()
    half = n // 2
    out[ys[:half], xs[:half]] = 255
    out[ys[half:], xs[half:]] = 0
    return out


def rotate3(img):
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), 3, 1.0)
    cos, sin = abs(m[0, 0]), abs(m[0, 1])
    nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    m[0, 2] += nw / 2 - w / 2
    m[1, 2] += nh / 2 - h / 2
    return cv2.warpAffine(img, m, (nw, nh), borderValue=(255, 255, 255))


def upscale2(img):
    return cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
