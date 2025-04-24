# main.py
"""End-to-end pipeline orchestration:
    - Generate synthetic timeline with real event names
    - Create paired direct/relative fact blocks
    - Auto-generate questions & compute gold answers
    - Evaluate a single variant (direct or relative) against an LLM
    - Persist a unified timeline JSON, per-run CSV, and metadata
"""
from __future__ import annotations

import argparse
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from event_library import load_events
from tuple_builder import TupleBuilder
from fact_synthesiser import synthesize_facts
from question_generator import generate_questions
from gold_engine import compute_answers
from dataset_writer import write_full_timeline, write_run_csv, write_metadata
from prompt_builder import build_prompt

load_dotenv()


def run_pipeline(args: argparse.Namespace) -> None:
    """Run a single pipeline iteration: generate, persist, evaluate, and log."""
    # Unique run/timeline ID
    run_id = uuid.uuid4().hex[:8]

    # 1. Load events by theme
    events = load_events(args.theme)

    # 2. Build synthetic timeline
    builder = TupleBuilder(rng_seed=args.seed)
    tuples = builder.build(
        events,
        tuple_size=args.tuple_size,
        total_tuples=args.total_tuples,
        wrong_order_prob=args.wrong_order_prob,
    )
    timeline = sorted([ev for tup in tuples for ev in tup], key=lambda e: e.start)

    # 3. Synthesize fact sets
    fact_direct = "\n".join(
        synthesize_facts(tuples, variant="ABS", rng_seed=args.seed, use_llm=False)
    )
    fact_relative = "\n".join(
        synthesize_facts(tuples, variant="REL", rng_seed=args.seed, use_llm=False)
    )

    # 4. Questions & gold answers
    questions = generate_questions(fact_direct, timeline, use_llm=False)
    gold_answers = compute_answers(timeline, questions)

    # 5. Persist full timeline JSON
    write_full_timeline(
        run_id,
        fact_direct,
        fact_relative,
        questions,
        gold_answers,
        [
            {"name": ev.name, "start": ev.start.isoformat(), "end": ev.end.isoformat(),
             "true_date": ev.true_date.isoformat() if ev.true_date else None}
            for ev in timeline
        ]
    )

    # 6. Select variant for evaluation
    fact_set = fact_direct if args.variant == "direct" else fact_relative

    # 7. Initialize LLM client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    client = OpenAI(api_key=api_key)

    # 8. Evaluate each question and score
    from comparator import score_row

    header = [
        "run_id", "question", "question_type", "model",
        "gold_answer", "model_answer", "correct"
    ]
    rows: List[Dict[str, Any]] = []

    for q in questions:
        prompt = build_prompt(fact_set, q["question"])
        resp = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        model_answer = resp.choices[0].message.content.strip()
        gold = gold_answers[q["id"]]
        correct = int(score_row(model_answer, gold))

        rows.append({
            "run_id": run_id,
            "question": q["question"],
            "question_type": q["templateID"],
            "model": args.model,
            "gold_answer": gold,
            "model_answer": model_answer,
            "correct": correct,
        })

    # 9. Write results CSV and metadata
    write_run_csv(run_id, rows, header)
    question_counts = {tpl: sum(1 for q in questions if q["templateID"] == tpl)
                       for tpl in set(q["templateID"] for q in questions)}
    write_metadata(run_id, args.model, args.variant, question_counts)

    print(f"Run {run_id} complete: runs/results_{run_id}.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Temporal Benchmark Pipeline")
    parser.add_argument("--theme", required=True, help="Filter events by theme")
    parser.add_argument("--tuple_size", type=int, default=2, help="Events per tuple")
    parser.add_argument("--total_tuples", type=int, default=10, help="Number of tuples to sample")
    parser.add_argument("--wrong_order_prob", type=float, default=0.0,
                        help="Probability to shuffle within-tuple")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--model", default="gpt-4", help="LLM model name")
    parser.add_argument("--variant", choices=["direct", "relative"],
                        default="direct", help="Which factset variant to evaluate")
    args = parser.parse_args()
    run_pipeline(args)
