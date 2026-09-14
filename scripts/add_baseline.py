"""Add a baseline entry from a real measured run record (re-baseline act).

Usage: python scripts/add_baseline.py <run-record.json> [--id N]

The run record is report/cer-run.json as written by
tests/model/test_cer_telemetry.py (provenance, generated, receipts,
avg_ocr_s, clean/blur means, m2_sums, per-receipt rows for all six
variants). The record is validated before anything is written:

- receipts == 20, every row has file/cer_clean/cer_blur (all in [0,1])
- row file set == data/golden/labels.json keys (real-data integrity)
- means recomputed from the rows match the record's stated means

The entry replaces any existing entry with the same (os_family,
tesseract_version) provenance, otherwise it is appended with the next free
id (or --id). `last_run` is never touched. Committing the result under a
logged order completes the re-baseline act (docs/quality-gates.md).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = os.path.join(ROOT, "data", "baselines", "metrics.json")
LABELS = os.path.join(ROOT, "data", "golden", "labels.json")


def fail(msg):
    print(f"DATA-ERR: {msg}")
    sys.exit(1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) > 1 else 1)
    rec_path = sys.argv[1]
    forced_id = None
    if "--id" in sys.argv:
        forced_id = int(sys.argv[sys.argv.index("--id") + 1])
    if not os.path.exists(rec_path):
        fail(f"run record not found: {rec_path}")
    with open(rec_path, encoding="utf-8") as fh:
        rec = json.load(fh)

    for k in ("provenance", "generated", "receipts", "avg_ocr_s",
              "clean_cer_mean", "blur_cer_mean", "m2_sums", "by_receipt"):
        if k not in rec:
            fail(f"run record missing key {k!r}")
    rows = rec["by_receipt"]
    if rec["receipts"] != 20 or len(rows) != 20:
        fail(f"expected 20 receipts, got receipts={rec.get('receipts')} rows={len(rows)}")
    for r in rows:
        for k in ("file", "cer_clean", "cer_blur"):
            if k not in r:
                fail(f"row missing key {k!r}: {r.get('file', '?')}")
        for k in ("cer_clean", "cer_blur"):
            if not 0.0 <= r[k] <= 1.0:
                fail(f"{r['file']} {k}={r[k]} outside [0,1]")
    with open(LABELS, encoding="utf-8") as fh:
        labels = json.load(fh)
    if set(r["file"] for r in rows) != set(labels.keys()):
        fail("record file set != data/golden/labels.json keys")
    for key in ("clean_cer_mean", "blur_cer_mean"):
        src = "cer_clean" if key.startswith("clean") else "cer_blur"
        recomputed = round(sum(r[src] for r in rows) / len(rows), 4)
        if recomputed != rec[key]:
            fail(f"{key}={rec[key]} != recomputed {recomputed} from rows")
    prov = rec["provenance"]
    for k in ("os_family", "tesseract_version"):
        if k not in prov:
            fail(f"record provenance missing {k!r}")

    if not os.path.exists(METRICS):
        fail(f"{METRICS} missing — run scripts/calibrate.py for the initial baseline first")
    with open(METRICS, encoding="utf-8") as fh:
        m = json.load(fh)
    if isinstance(m.get("baselines"), list):
        entries = m["baselines"]
    elif isinstance(m.get("baseline"), dict):  # legacy schema 2
        entries = [dict(m["baseline"], id=1)]
    else:
        fail("metrics.json has neither `baselines` nor legacy `baseline`")
    entries = [e for e in entries
               if not (e.get("provenance", {}).get("os_family") == prov["os_family"]
                       and e.get("provenance", {}).get("tesseract_version") == prov["tesseract_version"])]
    new_id = forced_id if forced_id is not None else max([e.get("id", 0) for e in entries] + [0]) + 1
    entry = {
        "id": new_id,
        "provenance": prov,
        "generated": rec["generated"],
        "receipts": rec["receipts"],
        "clean_cer_mean": rec["clean_cer_mean"],
        "blur_cer_mean": rec["blur_cer_mean"],
        "m2_sums": rec["m2_sums"],
        "avg_ocr_s": rec["avg_ocr_s"],
        "by_receipt": rows,
    }
    entries.append(entry)
    entries.sort(key=lambda e: e.get("id", 0))
    out = {"schema": 3, "baselines": entries, "last_run": m.get("last_run")}
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"OK: baseline #{new_id} <- {rec_path}")
    print(f"  provenance: {prov.get('os_family')}/Tesseract {prov.get('tesseract_version')}"
          f"/python {prov.get('python')}")
    print(f"  clean mean {entry['clean_cer_mean']:.4f}, blur mean {entry['blur_cer_mean']:.4f}, "
          f"generated {entry['generated']}")
    print(f"  entries now: {[e.get('id') for e in entries]} (last_run untouched)")


if __name__ == "__main__":
    main()
