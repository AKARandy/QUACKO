"""QUACKO V2 data fetcher — the Committed 20 (one-time, pin-verified).

Downloads exactly the 20 pinned SROIE Task-1 receipts from the
podbilabs/sroie-donut HF dataset, verifies each SHA256 against the pins
in the verified V1 manifest, and writes data/golden/{labels.json,
MANIFEST-20.sha256, PROVENANCE-20.md}. Any mismatch => DATA-ERR, exit 2.
Never substitutes, never generates, never downloads more than the 20.
"""
import hashlib
import json
import os
import sys

REPO_ID = os.environ.get("QUACKO_DATA_REPO", "podbilabs/sroie-donut")
REVISION = os.environ.get("QUACKO_DATA_REVISION", "main")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(ROOT, "data", "golden")
SRC_LABELS = os.path.join(GOLDEN, "labels.jsonl")
SRC_MANIFEST = os.path.join(GOLDEN, "MANIFEST.sha256")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
MAX_TOTAL_BYTES = 10 * 1024 * 1024


def fail(msg):
    print(f"DATA-ERR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def pinned_20():
    """(img_name, sha256) for the 20 — PLAN-V2 §2 deterministic selection rule,
    applied to the verified V1 labels + manifest (both read from disk)."""
    man = {}
    for line in open(SRC_MANIFEST, encoding="utf-8"):
        line = line.strip()
        if line:
            h, f = line.split()
            man[f] = h
    labels = [json.loads(l) for l in open(SRC_LABELS, encoding="utf-8")]
    first = {}
    for i, r in enumerate(labels):
        store = r["text"].split("\n")[0].strip().upper()
        first.setdefault(store, i)
    stores = sorted(first.items(), key=lambda kv: kv[1])
    n = len(stores)
    picks = sorted({stores[k * (n - 1) // 19] for k in range(20)}, key=lambda kv: kv[1])
    if len(picks) != 20:
        fail(f"selection rule produced {len(picks)} distinct stores, expected 20")
    out = []
    for _store, idx in picks:
        name = labels[idx]["file"]
        if name not in man:
            fail(f"no manifest hash for {name}")
        out.append((name, man[name]))
    return out, n


def main():
    try:
        from huggingface_hub import HfApi, hf_hub_download
    except ImportError:
        fail("`huggingface_hub` not installed — `pip install -r requirements.txt` first.")
    if not (os.path.exists(SRC_LABELS) and os.path.exists(SRC_MANIFEST)):
        fail("V1 source labels/manifest missing from data/golden — nothing to pin against")
    pins, store_count = pinned_20()
    pin_map = dict(pins)

    api = HfApi()
    try:
        info = api.repo_info(REPO_ID, repo_type="dataset", revision=REVISION)
    except Exception as exc:
        fail(f"cannot reach dataset {REPO_ID}@{REVISION}: {exc}")
    try:
        tree = api.list_repo_tree(REPO_ID, repo_type="dataset", revision=REVISION, recursive=True)
    except Exception as exc:
        fail(f"cannot list dataset tree: {exc}")

    paths = []
    for el in tree:
        if getattr(el, "type", None) == "directory":
            continue
        if os.path.splitext(el.path)[1].lower() in IMG_EXTS:
            paths.append(el.path)
    paths.sort()
    # V1 fetcher naming: img_NNNN<ext> in sorted walk order of the (flat) snapshot.
    src_for = {f"img_{i:04d}{os.path.splitext(p)[1].lower()}": p for i, p in enumerate(paths)}
    missing = [nm for nm in pin_map if nm not in src_for]
    if missing:
        fail(f"pinned names not resolvable in dataset listing: {missing}")
    print(f"dataset {REPO_ID}@{REVISION} commit {info.sha}: {len(paths)} images listed")

    gt = {}
    for l in open(SRC_LABELS, encoding="utf-8"):
        r = json.loads(l)
        gt[r["file"]] = r["text"]

    os.makedirs(GOLDEN, exist_ok=True)
    manifest = []
    total = 0
    for name, want in sorted(pin_map.items()):
        try:
            src = hf_hub_download(REPO_ID, src_for[name], repo_type="dataset", revision=REVISION)
        except Exception as exc:
            fail(f"download failed for {name} ({src_for[name]}): {exc}")
        with open(src, "rb") as fh:
            blob = fh.read()
        got = sha256_bytes(blob)
        if got != want:
            fail(f"SHA256 mismatch for {name}: pinned {want}, fetched {got}")
        with open(os.path.join(GOLDEN, name), "wb") as fh:
            fh.write(blob)
        total += len(blob)
        manifest.append((name, want))
        print(f"OK {name} {got[:12]}… ({len(blob)} bytes)")

    if total > MAX_TOTAL_BYTES:
        fail(f"Committed-20 total {total} bytes exceeds 10 MB repo-size gate")

    with open(os.path.join(GOLDEN, "labels.json"), "w", encoding="utf-8") as fh:
        json.dump({n: gt[n] for n, _ in manifest}, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(GOLDEN, "MANIFEST-20.sha256"), "w", encoding="utf-8") as fh:
        for n, h in manifest:
            fh.write(f"{h}  {n}\n")
    prov = [
        "# Provenance — Committed 20",
        "",
        f"- date: 2026-09-14",
        f"- source: {REPO_ID}@{REVISION} (HF dataset commit {info.sha})",
        f"- selection: PLAN-V2 §2 deterministic rule — one image per merchant store,",
        f"  evenly spaced k*(n-1)//19 over {store_count} distinct stores sorted by first appearance",
        f"- total size: {total} bytes (gate: <= {MAX_TOTAL_BYTES})",
        f"- every SHA256 verified against the V1 manifest at fetch time; tests re-verify on load",
        "",
    ]
    for n, h in manifest:
        prov.append(f"- {n}  {h}")
    with open(os.path.join(GOLDEN, "PROVENANCE-20.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(prov) + "\n")
    print(f"OK: 20 images committed to data/golden/ ({total} bytes total)")


if __name__ == "__main__":
    main()
