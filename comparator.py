# comparator.py
"""
Compare model answers to gold answers.

• Numeric answers (plain number or “N days”) are checked deterministically.
• All other answers are judged by an LLM verifier (YES/NO).
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import List, Dict
from difflib import SequenceMatcher
from llm_utils import llm_verdict, FUZZY_THRESHOLD, YES_TOKENS, NO_TOKENS

try:
    from openai import OpenAI
except ImportError:                       # pragma: no cover
    OpenAI = None                         # type: ignore

GROQ_LLAMA_MODEL = os.getenv("GROQ_LLAMA_MODEL", "groq:llama-3.3-70b-versatile")
FALLBACK_MARGIN = float(os.getenv("LLM_FALLBACK_MARGIN", "0.3"))  # margin for fuzzy fallback

# --------------------------------------------------------------------------- #
def _numeric_equal(a: str, b: str, tol: float = 0) -> bool:
    """
    Return True if numbers in a and b differ by ≤ tol.
    Recognises numeric substrings anywhere in the texts.
    """
    pattern = r"-?\d+(?:\.\d+)?"
    ma = re.search(pattern, a)
    mb = re.search(pattern, b)
    if not (ma and mb):
        return False
    a_num = float(ma.group())
    b_num = float(mb.group())
    return abs(a_num - b_num) <= tol

# --------------------------------------------------------------------------- #
def score_row(
    question: str,
    model_answer: str,
    gold_answer: str,
    use_llm: bool = False,
) -> bool:
    """Return True if the model answer is correct."""
    model_answer = model_answer.strip()
    gold_answer  = gold_answer.strip()
    # normalize for comparisons
    ma_lower = model_answer.lower()
    ga_lower = gold_answer.lower()

    # 1️⃣ duration list answers (multiple durations)
    if "," in ga_lower and all(part.strip().endswith(" days") for part in ga_lower.split(",")):
        ga_parts = [p.strip() for p in gold_answer.split(",")]
        ma_parts = [p.strip() for p in model_answer.split(",")]
        if len(ga_parts) != len(ma_parts):
            return False
        return all(_numeric_equal(ma, ga, tol=1) for ma, ga in zip(ma_parts, ga_parts))

    # 2️⃣ single duration answers
    if ga_lower.endswith(" days") and "," not in ga_lower:
        # allow ±1 day tolerance
        return _numeric_equal(model_answer, gold_answer, tol=1)

    # 3️⃣ numeric answers (plain number)
    if ga_lower.replace(" ", "").isdigit():
        return _numeric_equal(model_answer, gold_answer, tol=0)

    # 4️⃣ direct string match ignoring case
    if ma_lower == ga_lower:
        return True
    # 5️⃣ handle synonyms: None, yes/no (require exact 'none')
    if ga_lower == "none" and ma_lower == "none":
        return True
    if ga_lower in YES_TOKENS and ma_lower in YES_TOKENS:
        return True
    if ga_lower in NO_TOKENS and ma_lower in NO_TOKENS:
        return True
    # 6️⃣ list-of-names answers require strict exact match
    if "," in gold_answer and not any(ch.isdigit() for ch in ga_lower):
        return False
    # 7️⃣ fuzzy-match for other cases
    ratio = SequenceMatcher(None, ma_lower, ga_lower).ratio()
    if ratio >= FUZZY_THRESHOLD:
        return True
    # fallback only when ratio is close to threshold
    min_ratio = FUZZY_THRESHOLD - FALLBACK_MARGIN
    if ratio < min_ratio or not use_llm:
        return False
    # 8️⃣ LLM fallback
    return llm_verdict(question, gold_answer, model_answer,
                       model_name=GROQ_LLAMA_MODEL)

# --------------------------------------------------------------------------- #
def score_run_csv(
    infile: str | Path,
    outfile: str | Path | None = None,
    *,
    use_llm: bool = False,
    api_key: str | None = None,
):
    """Add/overwrite a 'correct' column in the run CSV."""
    rows: List[List[str]] = []
    with open(infile, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        for r in reader:
            rows.append(r)

    for col in ["question", "model_answer", "gold_answer"]:
        if col not in header:
            raise ValueError(f"CSV missing required column '{col}'")

    if "correct" not in header:
        header.append("correct")
    correct_idx = header.index("correct")

    for r in rows:
        q    = r[header.index("question")]
        pred = r[header.index("model_answer")]
        gold = r[header.index("gold_answer")]

        verdict = score_row(q, pred, gold, use_llm)
        if len(r) < len(header):
            r.append(str(int(verdict)))
        else:
            r[correct_idx] = str(int(verdict))

    out = Path(outfile) if outfile else Path(infile)
    with out.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(header)
        csv.writer(fh).writerows(rows)

# CLI ---------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse, os

    p = argparse.ArgumentParser(description="Score run CSV with LLM verification")
    p.add_argument("in_csv", help="Input results CSV")
    p.add_argument("out_csv", nargs="?", help="Output CSV (default: overwrite)")
    p.add_argument("--use_llm", action="store_true", help="Enable LLM verification")
    p.add_argument("--api_key", default=os.getenv("OPENAI_API_KEY"),
                   help="OpenAI API key (env var fallback)")
    args = p.parse_args()

    score_run_csv(args.in_csv, args.out_csv,
                  use_llm=args.use_llm, api_key=args.api_key)
