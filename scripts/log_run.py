"""Merge real pytest pass rates (junit xml) into data/baselines/metrics.json.
Reads only what a real run produced; never invents rates."""
import json
import os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = os.path.join(ROOT, "data", "baselines", "metrics.json")


def layer_of(classname: str):
    if classname.startswith("tests.api"):
        return "api"
    if classname.startswith("tests.model"):
        return "model"
    if classname.startswith("tests.ui") or "upload.spec" in classname:
        return "ui"
    return None


def main():
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
    if not stats:
        print("log_run: no junit results found — metrics.json untouched")
        return
    m = {}
    if os.path.exists(METRICS):
        with open(METRICS, encoding="utf-8") as fh:
            m = json.load(fh)
    pr = m.get("pass_rate", {})
    for layer, t in stats.items():
        if t["n"]:
            pr[layer] = round((t["n"] - t["fail"]) / t["n"], 4)
    m["pass_rate"] = pr
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2)
    print(f"log_run: pass_rate = {json.dumps(pr)}")


if __name__ == "__main__":
    main()
