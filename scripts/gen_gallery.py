"""Render docs/failure-gallery.md from a real failures dir (report/failures).

Generated on every deploy. Entries become a thumbnail grid; clicking a card
opens a lightbox with input vs degraded variant vs ground truth
(wired by docs/js/gallery.js). An empty gallery says so explicitly.
Image paths are relative to the gallery page (../assets/...).
"""
import datetime
import html
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_text(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read().rstrip()
    return ""


def main():
    src = os.path.join(ROOT, "report", "failures")
    dst = os.path.join(ROOT, "docs", "failure-gallery.md")
    # Drop stale copied images: the gallery only ever shows the current run.
    shutil.rmtree(os.path.join(ROOT, "docs", "assets", "failures"), ignore_errors=True)
    names = []
    if os.path.isdir(src):
        for d in sorted(os.listdir(src)):
            if os.path.isdir(os.path.join(src, d)):
                names.append(d)
    lines = [
        "# Failure Gallery",
        "",
        f"Generated {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')} "
        "by `scripts/gen_gallery.py` from **real test failures only**: click any "
        "card to inspect input vs degraded variant vs ground truth.",
        "",
    ]
    if not names:
        lines += [
            '<div class="qk-empty"><b>No failures in the latest run.</b><br><br>',
            "This page is regenerated on every deploy to `main`. If a model-quality test fails, "
            "the failing image, its degraded variant, the ground truth, the prediction, and the "
            "defect class are captured here automatically.</div>",
            "",
        ]
    else:
        lines.append('<div class="qk-gal-grid" id="qk-gal">')
        for name in names:
            p = os.path.join(src, name)
            m = {}
            mp = os.path.join(p, "metrics.json")
            if os.path.exists(mp):
                with open(mp, encoding="utf-8") as fh:
                    m = json.load(fh)
            dest_dir = os.path.join(ROOT, "docs", "assets", "failures", name)
            os.makedirs(dest_dir, exist_ok=True)
            rel = f"../assets/failures/{name}"
            has_input, has_deg = False, False
            ip = os.path.join(p, "input.png")
            if os.path.exists(ip):
                shutil.copy(ip, os.path.join(dest_dir, "input.png"))
                has_input = True
            dp = os.path.join(p, "degraded.png")
            if os.path.exists(dp):
                shutil.copy(dp, os.path.join(dest_dir, "degraded.png"))
                has_deg = True
            thumb = f"{rel}/input.png" if has_input else ""
            cer = m.get("cer", "?")
            dclass = m.get("defect_class", "unclassified")
            title = html.escape(name, quote=True)
            lines += [
                f'<figure class="qk-gal-card" tabindex="0" role="button" data-title="{title}"',
                f'  data-input="{rel}/input.png" data-degraded="{(rel + "/degraded.png") if has_deg else ""}">',
                (f'  <img src="{thumb}" alt="input {title}" loading="lazy">' if thumb
                 else '  <div class="qk-fallback">no image captured</div>'),
                f"  <figcaption><b>{html.escape(name)}</b>"
                f"<span>CER {html.escape(str(cer))} · {html.escape(str(dclass))}</span></figcaption>",
                '  <div class="qk-gal-data" hidden>',
                f"    <div data-k=\"assertion\">{html.escape(str(m.get('assertion', '?')))}</div>",
                f"    <div data-k=\"test\">{html.escape(str(m.get('test', '?')))}</div>",
                f"    <div data-k=\"cer\">{html.escape(str(cer))}</div>",
                f"    <div data-k=\"class\">{html.escape(str(dclass))}</div>",
                f"    <pre data-k=\"gt\">{html.escape(read_text(os.path.join(p, 'gt.txt')))}</pre>",
                f"    <pre data-k=\"pred\">{html.escape(read_text(os.path.join(p, 'pred.txt')))}</pre>",
                "  </div>",
                "</figure>",
            ]
        lines += [
            "</div>",
            "",
            '<div class="qk-modal" id="qk-modal" hidden>',
            '  <div class="qk-modal-box" role="dialog" aria-modal="true">',
            '    <button class="qk-modal-x" id="qk-modal-x" type="button">Close</button>',
            '    <h3 id="qk-m-title"></h3>',
            '    <p class="qk-m-assert" id="qk-m-assert"></p>',
            '    <div class="qk-m-imgs">',
            '      <figure><img id="qk-m-input" alt="input image"><figcaption>Input</figcaption></figure>',
            '      <figure id="qk-m-degraded-fig"><img id="qk-m-degraded" alt="degraded variant"><figcaption>Degraded variant</figcaption></figure>',
            "    </div>",
            '    <div class="qk-m-texts">',
            "      <div><h4>Ground truth</h4><pre id=\"qk-m-gt\"></pre></div>",
            "      <div><h4>Prediction</h4><pre id=\"qk-m-pred\"></pre></div>",
            "    </div>",
            "  </div>",
            "</div>",
            "",
        ]
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"OK: {len(names)} failure(s) -> {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    main()
