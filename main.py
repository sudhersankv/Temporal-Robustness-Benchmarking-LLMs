# main.py
"""End-to-end temporal benchmark:
    - Build synthetic timeline
    - Generate direct + relative fact blocks
    - Generate questions and gold answers
    - Evaluate both variants using the model
    - Score with rule-based + optional LLM fallback
    - Persist results and metadata
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from llm_utils import chat_complete

from run_id_manager import next_run_id
from event_library import load_events
from tuple_builder import TupleBuilder
from fact_synthesiser import synthesize_facts
from question_generator import generate_questions
from gold_engine import compute_answers
from dataset_writer import write_full_timeline, write_run_csv, write_metadata
from prompt_builder import build_prompt
from comparator import score_row

load_dotenv()

def run_pipeline(args: argparse.Namespace) -> None:
    run_id = next_run_id()

    # 1. Load and sample events (ignore theme if 'all')
    theme = None if args.theme.lower() == "all" else args.theme
    events = load_events(theme)
    builder = TupleBuilder(
        rng_seed=args.seed,
        max_overlap=args.max_overlap,
        jitter=args.jitter,
    )
    tuples = builder.build(
        events,
        tuple_size=args.tuple_size,
        total_tuples=args.total_tuples,
        wrong_order_prob=args.wrong_order_prob
    )
    full_tl = sorted([ev for tup in tuples for ev in tup], key=lambda e: e.start)
    # limit events per fact set
    timeline = full_tl[: args.max_events]

    # 2. Fact sets (use only limited timeline)
    direct_facts = synthesize_facts(
        timeline,
        variant="ABS",
        rng_seed=args.seed,
        abs_format=args.abs_format,
        shuffle_abs=args.shuffle_abs,
    )
    fact_direct = "\n".join(direct_facts)

    relative_facts = synthesize_facts(
        timeline,
        variant="REL",
        rng_seed=args.seed,
        shuffle_rel=args.shuffle_rel,
    )
    fact_relative = "\n".join(relative_facts)

    # 3. Questions + gold answers
    questions = generate_questions(fact_direct, timeline)
    gold_answers = compute_answers(timeline, questions)

    # 4. Persist timeline
    write_full_timeline(
        run_id, fact_direct, fact_relative, questions, gold_answers,
        [
            {
                "name": ev.name,
                "start": ev.start.isoformat(),
                "end": ev.end.isoformat(),
                "true_date": ev.true_date.isoformat() if ev.true_date else None
            }
            for ev in timeline
        ]
    )

    # 5. Use chat_complete for answer generation across all LLMs

    # 6. Evaluate both variants
    rows: List[Dict[str, Any]] = []
    header = [
        "fact_id", "question", "template", "gold_answer",
        "direct_model_answer", "relative_model_answer",
        "direct_correct", "relative_correct", "model"
    ]

    for q in questions:
        prompt_d = build_prompt(fact_direct, q["question"])
        ans_d = chat_complete(prompt_d, model_name=args.model).strip()

        prompt_r = build_prompt(fact_relative, q["question"])
        ans_r = chat_complete(prompt_r, model_name=args.model).strip()

        gold = gold_answers[q["id"]]
        corr_d = int(score_row(q["question"], ans_d, gold))
        corr_r = int(score_row(q["question"], ans_r, gold))


        rows.append({
            "fact_id": run_id,
            "question": q["question"],
            "template": q["templateID"],
            "gold_answer": gold,
            "direct_model_answer": ans_d,
            "relative_model_answer": ans_r,
            "direct_correct": corr_d,
            "relative_correct": corr_r,
            "model": args.model
        })

    # 7. Write output
    write_run_csv(run_id, rows, header)
    question_counts = {
        tpl: sum(1 for q in questions if q["templateID"] == tpl)
        for tpl in set(q["templateID"] for q in questions)
    }
    write_metadata(run_id, args.model, "both", question_counts)

    print(f"✅ Run {run_id} complete → runs/results_{run_id}.csv")


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Temporal robustness benchmark")
    parser.add_argument(
        "--theme",
        default="all",
        help="Event theme (case-insensitive) or 'all' for no filtering",
    )
    parser.add_argument("--tuple_size", type=int, default=3)
    parser.add_argument("--total_tuples", type=int, default=8)
    parser.add_argument("--wrong_order_prob", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--model", default="gemini:gemini-2.0-flash")
    parser.add_argument("--max_overlap", type=int, default=0,
                        help="Max days overlap between consecutive events")
    parser.add_argument("--jitter", type=int, default=0,
                        help="Max jitter days to apply to event dates")
    parser.add_argument("--abs_format", choices=["sentence", "inline", "list"],
                        default="sentence",
                        help="Format for absolute fact set")
    parser.add_argument("--shuffle_abs", action="store_true",
                        help="Shuffle narrative order for absolute fact-set")
    parser.add_argument("--shuffle_rel", action="store_true",
                        help="Shuffle narrative order for relative fact-set")
    parser.add_argument("--max_events", type=int, default=12,
                        help="Max number of events per fact set (10-15 recommended)")
    args = parser.parse_args()
    run_pipeline(args)
