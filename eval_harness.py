# eval_harness.py
"""Run datasets against a target LLM and record responses + latency.

Usage example
-------------
>>> from eval_harness import Evaluator
>>> ev = Evaluator(model_name="gpt-4o-mini", outfile="runs/gpt4o_run.csv")
>>> ev.eval_dataset("processed_testcases/timeline_01_direct.json")
"""
from __future__ import annotations

import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

from dataset_writer import load_dataset
from prompt_builder import build_prompt

__all__ = ["Evaluator"]

HEADER = [
    "timestamp",
    "dataset_path",
    "variant",
    "question_id",
    "model",
    "prompt_tokens",
    "completion_tokens",
    "latency_sec",
    "gold_answer",
    "model_answer",
]

# ---------------------------------------------------------------------------
class Evaluator:
    """Wraps LLM API calls and writes row‑wise CSV logs."""

    def __init__(self, model_name: str, *, outfile: str | Path):
        if OpenAI is None:
            raise RuntimeError("openai package not installed – cannot evaluate")
        self.client = OpenAI()
        self.model = model_name
        self.outfile = Path(outfile)
        if not self.outfile.parent.exists():
            self.outfile.parent.mkdir(parents=True)
        # create CSV with header if new file
        if not self.outfile.exists():
            with self.outfile.open("w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(HEADER)

    # ------------------------------------------------------------------
    def _log(self, row: Dict):
        with self.outfile.open("a", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow([row[h] for h in HEADER])

    # ------------------------------------------------------------------
    def eval_dataset(self, dataset_path: str | Path):
        ds = load_dataset(dataset_path)
        variant = "direct" if "_direct" in str(dataset_path) else "relative"
        gold_map = ds["expected_answers"]

        for q in ds["questions"]:
            prompt = build_prompt(ds["fact_set"], q["question"])
            t0 = time.time()
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            latency = time.time() - t0
            choice = resp.choices[0].message
            model_answer = choice.content.strip()
            row = {
                "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
                "dataset_path": str(dataset_path),
                "variant": variant,
                "question_id": q["id"],
                "model": self.model,
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else "",
                "completion_tokens": resp.usage.completion_tokens if resp.usage else "",
                "latency_sec": f"{latency:.2f}",
                "gold_answer": gold_map[str(q["id"])] if str(q["id"]) in gold_map else gold_map[q["id"]],
                "model_answer": model_answer,
            }
            self._log(row)
