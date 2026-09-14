"""Field-anchored CER (PLAN-V2 §3.2).

GT for the Committed 20 is 4 key fields per receipt (name / date / address /
total), NOT full-page transcription.

CER = Σ ed / Σ len(field) where ed = min over OCR line groups (1-3 consecutive
lines, space-joined) of the semi-global edit distance between the normalized
GT field and ANY SUBSTRING of the group. Semi-global (edit-distance to a
substring) means extra OCR content surrounding a correctly read field
(timestamps after dates, column labels around totals) does not penalize it;
a field absent from the OCR output costs its full length. Pure-Python
Levenshtein, no extra dependency.
"""
import re
import unicodedata


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower()
    s = re.sub(r"[^a-z0-9.\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _semi_global(needle: str, hay: str) -> int:
    """Exact min edit distance between needle and any substring of hay."""
    m, n = len(needle), len(hay)
    if m == 0:
        return 0
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        na = needle[i - 1]
        for j in range(1, n + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (na != hay[j - 1]))
        prev = cur
    return min(prev)


def field_cer(gt_text: str, ocr_text: str):
    """Return (cer, per_field_detail). cer = Σed/Σlen over GT fields."""
    gt_fields = [norm(line) for line in (gt_text or "").splitlines() if norm(line)]
    ocr_lines = [norm(l) for l in (ocr_text or "").splitlines() if norm(l)]
    total_ed = 0
    total_len = 0
    detail = []
    for f in gt_fields:
        if not ocr_lines:
            total_ed += len(f)
            total_len += len(f)
            detail.append((f, 1.0))
            continue
        fw = set(w for w in f.split() if len(w) >= 2)
        scored = []
        for i, l in enumerate(ocr_lines):
            scored.append((len(fw & set(l.split())), i))
        scored.sort(reverse=True)
        idxs = [i for ov, i in scored if ov > 0][:24] or list(range(len(ocr_lines)))
        best = len(f)
        for i in idxs:
            if best == 0:
                break
            cands = [ocr_lines[i]]
            if i + 1 < len(ocr_lines):
                cands.append(ocr_lines[i] + " " + ocr_lines[i + 1])
            if i + 2 < len(ocr_lines):
                cands.append(cands[-1] + " " + ocr_lines[i + 2])
            for g in cands:
                if len(g) > 5 * len(f):
                    continue
                d = _semi_global(f, g)
                if d < best:
                    best = d
        total_ed += best
        total_len += len(f)
        detail.append((f, best / len(f)))
    return (total_ed / total_len if total_len else 0.0), detail
