# dataset_writer.py
"""Persist complete timeline JSON and per-run evaluation artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path("processed_testcases")
RUNS_DIR = Path("runs")
DATA_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True)

_SCHEMA_KEYS = {"id", "fact_set_direct", "fact_set_relative", "questions", "gold_answers", "timeline"}

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _validate_dataset(obj: Dict[str, Any]):
    missing = _SCHEMA_KEYS - obj.keys()
    if missing:
        raise ValueError(f"Dataset missing keys: {missing}")
    if not isinstance(obj["questions"], list):
        raise ValueError("questions must be a list")
    if not isinstance(obj["gold_answers"], dict):
        raise ValueError("gold_answers must be a dict")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_full_timeline(
    timeline_id: str,
    fact_direct: str,
    fact_relative: str,
    questions: List[Dict[str, Any]],
    gold_answers: Dict[int, str],
    timeline: List[Dict[str, Any]]
) -> Path:
    """Write the full JSON for a timeline (both variants + meta)."""
    obj = {
        "id": timeline_id,
        "fact_set_direct": fact_direct,
        "fact_set_relative": fact_relative,
        "questions": questions,
        "gold_answers": gold_answers,
        "timeline": timeline
    }
    _validate_dataset(obj)

    path = DATA_DIR / f"timeline_{timeline_id}.json"
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_run_csv(
    run_id: str,
    rows: List[Dict[str, Any]],
    header: List[str]
) -> Path:
    """Write evaluation rows to a CSV with run-specific name."""
    path = RUNS_DIR / f"results_{run_id}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        import csv
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_metadata(
    run_id: str,
    model: str,
    variant: str,
    question_counts: Dict[str, int]
) -> Path:
    """Write a small JSON with run metadata."""
    meta = {
        "run_id": run_id,
        "model": model,
        "variant": variant,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        "question_distribution": question_counts
    }
    path = RUNS_DIR / f"meta_{run_id}.json"
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
