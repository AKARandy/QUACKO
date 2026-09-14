"""QUACKO SUT — Flask + Tesseract. Response shape locked (PLAN-V2 §3.1)."""
import io
import json
import os

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, UnidentifiedImageError

from ocr_engine import ocr_bytes

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
METRICS = os.path.join(ROOT, "data", "baselines", "metrics.json")

app = Flask(
    __name__,
    static_folder=os.path.join(BASE, "static"),
    template_folder=os.path.join(BASE, "templates"),
)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MiB -> 413 above this

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


@app.get("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "engine": "tesseract"})


@app.get("/api/stats")
def stats():
    """Dashboard data (schema 3). Real run data only — explicit no-run state,
    never placeholder numbers (NO-LARP). Serves the latest measured run
    (`last_run`, else the first `baselines` entry) as a flat object, plus
    provenance of both sections for the footer."""
    if not os.path.exists(METRICS):
        return jsonify({"status": "no-run"})
    with open(METRICS, encoding="utf-8") as fh:
        m = json.load(fh)
    fallbacks = m.get("baselines") or ([m["baseline"]] if m.get("baseline") else [])
    run = m.get("last_run") or (fallbacks[0] if fallbacks else None)
    if not run:
        return jsonify({"status": "no-run"})
    out = {"status": "ok", "source": "last_run" if m.get("last_run") else "baseline"}
    for k in ("generated", "receipts", "clean_cer_mean", "blur_cer_mean", "avg_ocr_s",
              "m2_sums", "by_receipt", "pass_rate", "provenance"):
        if k in run:
            out[k] = run[k]
    if fallbacks and fallbacks[0].get("provenance"):
        out["baseline_provenance"] = fallbacks[0]["provenance"]
    return jsonify(out)


@app.post("/api/ocr")
def ocr():
    f = request.files.get("image")
    if f is None or not f.filename:
        return jsonify({"error": "missing file 'image'"}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        return jsonify({"error": f"invalid type '{ext}'"}), 400
    data = f.read()
    try:
        im = Image.open(io.BytesIO(data))
        im.verify()
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "not a valid image"}), 400
    try:
        result = ocr_bytes(data)
    except Exception as exc:  # surface real engine failures, never stub output
        return jsonify({"error": f"ocr engine failure: {exc}"}), 500
    return jsonify(
        {
            "text": result["text"],
            "confidence": result["confidence"],
            "boxes": result["boxes"],
        }
    )


@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "payload too large (max 8 MiB)"}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
