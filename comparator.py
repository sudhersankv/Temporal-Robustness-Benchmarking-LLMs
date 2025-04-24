# comparator.py
"""Compare model answers in the run CSV to gold and emit verdict + error tag."""
from __future__ import annotations

import csv
from difflib import SequenceMatcher
from pathlib import Path
from typing import List

__all__ = ["score_run_csv"]

THRESHOLD = 0.9  # fuzzy similarity for string answers

# ---------------------------------------------------------------------------

def _numeric_equal(a: str, b: str, tol: int = 0) -> bool:
    try:
        return abs(int(a.split()[0]) - int(b.split()[0])) <= tol
    except ValueError:
        return False


def _string_similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= THRESHOLD


# ---------------------------------------------------------------------------

def score_row(model_answer: str, gold_answer: str) -> bool:
    """Return True if model_answer is considered correct."""
    # numeric
    if gold_answer.replace(" ", "").isdigit():
        return _numeric_equal(model_answer, gold_answer)
    # numeric with 'days'
    if gold_answer.endswith(" days"):
        return _numeric_equal(model_answer, gold_answer, tol=0)
    # fallback string fuzzy
    return _string_similar(model_answer, gold_answer)


# ---------------------------------------------------------------------------

def score_run_csv(infile: str | Path, outfile: str | Path | None = None):
    """Add correctness column to an evaluation CSV (in‑place or to new file)."""
    rows: List[List[str]] = []
    header: List[str]

    with open(infile, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        for r in reader:
            rows.append(r)

    # ensure columns exist
    if "correct" not in header:
        header.append("correct")
    correct_idx = header.index("correct")

    for r in rows:
        gold = r[header.index("gold_answer")]
        pred = r[header.index("model_answer")]
        verdict = score_row(pred, gold)
        if len(r) < len(header):
            r.append(str(int(verdict)))
        else:
            r[correct_idx] = str(int(verdict))

    out = Path(outfile) if outfile else Path(infile)
    with out.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(header)
        csv.writer(fh).writerows(rows)


# CLI ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python comparator.py <run.csv> [scored.csv]")
        sys.exit(1)
    score_run_csv(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
