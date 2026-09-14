"""Merge a real run's results into the `last_run` section of
data/baselines/metrics.json (schema 3, Option C architecture).

Sources (all from this run): report/junit-api-model.xml + report/junit-ui.xml
(pass rates) and report/cer-run.json (measured CER telemetry + provenance).
The `baselines` list is NEVER touched here — re-baselining is an explicit,
logged act (scripts/calibrate.py, scripts/add_baseline.py). No rate or value
is invented: absent inputs are simply absent from the output.
"""
import json
import os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = os.path.join(ROOT, "data", "baselines", "metrics.json")
CER_RUN = os.path.join(ROOT, "report", "cer-run.json")
RUN_FIELDS = (
    "provenance",
    "generated",
    "receipts",
    "avg_ocr_s",
    "clean_cer_mean",
    "blur_cer_mean",
    "m2_sums",
    "by_receipt",
)


def layer_of(classname: str):
    if classname.startswith("tests.api"):
        return "api"
    if classname.startswith("tests.model"):
        return "model"
    if classname.startswith("tests.ui") or "upload.spec" in classname:
        return "ui"
    return None


def parse_junit():
    stats = {}
    for x in ("report/junit-api-model.xml", "report/junit-ui.xml"):
        p = os.path.join(ROOT, x)
        if not os.path.exists(p):
            continue
        root = ET.parse(p).getroot()
        for tc in root.iter("testcase"):
            layer = layer_of(tc.get("classname", ""))
            if layer is None:
                continue
            t = stats.setdefault(layer, {"n": 0, "fail": 0})
            t["n"] += 1
            if tc.find("failure") is not None or tc.find("error") is not None:
                t["fail"] += 1
    return stats


def main():
    stats = parse_junit()
    cer = None
    if os.path.exists(CER_RUN):
        with open(CER_RUN, encoding="utf-8") as fh:
            cer = json.load(fh)
    if not stats and cer is None:
        print("log_run: no junit results and no cer-run.json found — metrics.json untouched")
        return

    m = {}
    if os.path.exists(METRICS):
        with open(METRICS, encoding="utf-8") as fh:
            m = json.load(fh)
    if m.get("schema") == 2 and isinstance(m.get("baseline"), dict):  # legacy
        m = {"schema": 3, "baselines": [dict(m["baseline"], id=1)],
             "last_run": m.get("last_run")}
    if m.get("schema") != 3 or not isinstance(m.get("baselines"), list):
        m = {"schema": 3, "baselines": m.get("baselines") if isinstance(m.get("baselines"), list) else [],
             "last_run": m.get("last_run") if isinstance(m.get("last_run"), dict) else {}}

    last = cer if cer is not None else dict(m.get("last_run") or {})
    if stats:
        pr = dict(last.get("pass_rate") or {})
        for layer, t in stats.items():
            if t["n"]:
                pr[layer] = round((t["n"] - t["fail"]) / t["n"], 4)
        last["pass_rate"] = pr
    m["last_run"] = last

    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2)
    print(f"log_run: last_run written (pass_rate={json.dumps(last.get('pass_rate', {}))})")


if __name__ == "__main__":
    main()
