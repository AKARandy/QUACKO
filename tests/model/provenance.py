"""Run provenance (Option C addendum, 2026-09-14): OS + Tesseract version +
pipeline. Every field is measured at call time — never assumed.
Required in both metrics.json sections (baseline + last_run) so an
environment delta (e.g. local Tesseract 5.5.0 vs CI apt build) is visible."""
import datetime
import os
import platform
import sys

import pytesseract

import ocr_engine

_FAMILY = {"nt": "windows", "darwin": "macos"}


def get_provenance() -> dict:
    sysname = os.name
    return {
        "os": platform.platform(),
        "os_family": _FAMILY.get(sysname, platform.system().lower()),
        "tesseract_version": str(pytesseract.get_tesseract_version()),
        "python": sys.version.split()[0],
        "pipeline": (
            f"gray+normalize({ocr_engine.MIN_SIDE}-{ocr_engine.MAX_SIDE})"
            f"+gated-deskew+psm{ocr_engine.PSM}"
        ),
    }


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
