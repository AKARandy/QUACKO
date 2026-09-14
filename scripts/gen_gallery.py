"""Render docs/failure-gallery.md from a real failures dir (report/failures).
Generated on every deploy; an empty gallery says so explicitly."""
import datetime
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    src = os.path.join(ROOT, "report", "failures")
    dst = os.path.join(ROOT, "docs", "failure-gallery.md")
    entries = []
    if os.path.isdir(src):
        for d in sorted(os.listdir(src)):
            p = os.path.join(src, d)
            if os.path.isdir(p):
                entries.append((d, p))
    lines = [
        "# Failure Gallery",
        "",
        f"Generated {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')} "
        "by `scripts/gen_gallery.py` from **real test failures only** — every entry below is a "
        "captured miss: input | degraded variant | ground truth | prediction | defect class.",
        "",
    ]
    if not entries:
        lines += [
            "**No failures in the latest run.**",
            "",
            "This page is regenerated on every deploy to `main`. If a model-quality test fails, "
            "the failing image, its degraded variant, the ground truth, the prediction, and the "
            "defect class are captured here automatically.",
        ]
    for name, p in entries:
        m = {}
        mp = os.path.join(p, "metrics.json")
        if os.path.exists(mp):
            with open(mp, encoding="utf-8") as fh:
                m = json.load(fh)
        lines += [
            f"## {name}",
            "",
            f"- defect class: **{m.get('defect_class', 'unclassified')}**",
            f"- assertion: `{m.get('assertion', '?')}`",
            f"- CER: {m.get('cer', '?')}",
            f"- test: `{m.get('test', '?')}`",
            "",
        ]
        for img in ("input.png", "degraded.png"):
            ip = os.path.join(p, img)
            if os.path.exists(ip):
                dest_dir = os.path.join(ROOT, "docs", "assets", "failures", name)
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy(ip, os.path.join(dest_dir, img))
                lines.append(f"![{img}](assets/failures/{name}/{img})")
                lines.append("")
        for txt in ("gt.txt", "pred.txt"):
            tp = os.path.join(p, txt)
            if os.path.exists(tp):
                with open(tp, encoding="utf-8") as fh:
                    content = fh.read().rstrip()
                lines += [f"`{txt}`:", "```", content, "```", ""]
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"OK: {len(entries)} failure(s) -> {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    main()
