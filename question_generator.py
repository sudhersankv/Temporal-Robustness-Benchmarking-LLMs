# question_generator.py
"""Generate balanced question sets from a fact block using LLM‑B.

The generator produces JSON‑serialisable dicts with
    id, question, templateID, arguments
where *templateID* matches a deterministic answer function in *gold_engine.py*.

When no OpenAI key is available, the module falls back to a **deterministic
rule‑driven generator** that simply walks through pre‑defined template
functions and instantiates arguments drawn from the supplied timeline.  This
ensures CI coverage without external calls.
"""
from __future__ import annotations

import itertools
import json
import random
from pathlib import Path
from typing import Dict, List, Sequence

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

from tuple_builder import SyntheticEvent

# ---------------------------------------------------------------------------
# Template catalogue (must sync with gold_engine)
# ---------------------------------------------------------------------------
TEMPLATES = {
    "order.full": 1,
    "order.reverse": 1,
    "order.nth": 4,          # needs arg n
    "dur.single": 4,
    "dur.longest": 1,
    "dur.shortest": 1,       # new template for shortest duration
    "order.first": 4,        # new template for first occurrence comparison
    "order.first_last": 1,   # new template for first and last events
    "int.between": 4,
}

# ---------------------------------------------------------------------------
# Helper / deterministic generator
# ---------------------------------------------------------------------------

def _deterministic_questions(timeline: List[SyntheticEvent], max_q: int = 10) -> List[Dict]:
    """Return a small fixed set of deterministic questions for CI/offline use."""
    qs: List[Dict] = []
    qid = 1

    # 1. full order
    qs.append({
        "id": qid,
        "templateID": "order.full",
        "question": "List the events in chronological order.",
        "arguments": {},
    }); qid += 1

    # 2. reverse order
    qs.append({
        "id": qid,
        "templateID": "order.reverse",
        "question": "Give the events in reverse chronological order.",
        "arguments": {},
    }); qid += 1

    # 3. nth (choose random within range)
    n = random.randint(1, len(timeline))
    suffix = _ordinal_suffix(n)
    qs.append({
        "id": qid,
        "templateID": "order.nth",
        "question": f"What is the {n}{suffix} event chronologically?",
        "arguments": {"n": n},
    }); qid += 1

    # 4. duration single (random event)
    ev = random.choice(timeline)
    qs.append({
        "id": qid,
        "templateID": "dur.single",
        "question": f"How long did {ev.name} last?",
        "arguments": {"event": ev.name},
    }); qid += 1

    # 5. duration longest
    qs.append({
        "id": qid,
        "templateID": "dur.longest",
        "question": "Which event lasted the longest?",
        "arguments": {},
    }); qid += 1

    # 6. duration shortest
    qs.append({
        "id": qid,
        "templateID": "dur.shortest",
        "question": "Which event lasted the shortest?",
        "arguments": {},
    }); qid += 1

    # 7. first occurrence comparison
    a, b = random.sample(timeline, 2)
    qs.append({
        "id": qid,
        "templateID": "order.first",
        "question": f"Which out of {a.name} and {b.name} occurred first?",
        "arguments": {"event_A": a.name, "event_B": b.name},
    }); qid += 1

    # 8. first and last events
    qs.append({
        "id": qid,
        "templateID": "order.first_last",
        "question": "What is the first and last event in chronological order?",
        "arguments": {},
    }); qid += 1

    # 9. interval between two random distinct events
    a, b = random.sample(timeline, 2)
    qs.append({
        "id": qid,
        "templateID": "int.between",
        "question": f"What is the duration between the end of {a.name} and the start of {b.name}?",
        "arguments": {"event_A": a.name, "event_B": b.name},
    })

    return qs[:max_q]


def _ordinal_suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

# ---------------------------------------------------------------------------
# LLM generator wrapper
# ---------------------------------------------------------------------------

def generate_questions(
    fact_block: str,
    timeline: Sequence[SyntheticEvent],
    *,
    distribution: Dict[str, int] | None = None,
    use_llm: bool = False,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> List[Dict]:
    """Return list of structured question dicts.

    Parameters
    ----------
    fact_block : str
        The ABSOLUTE fact block shown to the question‑authoring LLM.
    timeline : list[SyntheticEvent]
        Needed to sample argument values.
    distribution : {templateID: count}
        Target counts per template. None → default small set.
    use_llm : bool
        If False, deterministic fallback is used (suitable for tests).
    """
    if not use_llm:
        return _deterministic_questions(list(timeline))

    if OpenAI is None:
        raise RuntimeError("openai package not installed; cannot use LLM mode")

    client = OpenAI()
    target_counts = distribution or {k: 1 for k in TEMPLATES}

    sys_prompt = (
        "You are an expert dataset curator. Given a block of factual sentences, "
        "output a JSON array of questions. Each entry must include:\n"
        "  • id  – unique integer\n"
        "  • question – the natural language question\n"
        "  • templateID – one of: " + ", ".join(TEMPLATES) + "\n"
        "  • arguments – JSON dict holding required parameters for that template\n\n"
        "Rules:\n"
        "  1. Distribute questions according to the requested counts.\n"
        "  2. NEVER invent events not in the fact block.\n"
        "  3. Do not output any commentary. Return only JSON."
    )

    user_prompt = json.dumps(
        {
            "facts": fact_block,
            "target_counts": target_counts,
        },
        ensure_ascii=False,
        indent=2,
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )

    raw_json = completion.choices[0].message.content
    try:
        questions = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\n{raw_json[:200]}")

    _validate_questions(questions, target_counts)
    return questions


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_questions(questions: List[Dict], target_counts: Dict[str, int]):
    seen_ids = set()
    counts = {k: 0 for k in target_counts}
    required_keys = {"id", "question", "templateID", "arguments"}

    for q in questions:
        if not required_keys.issubset(q):
            raise ValueError(f"Missing keys in question dict: {q}")
        if q["id"] in seen_ids:
            raise ValueError(f"Duplicate question id: {q['id']}")
        seen_ids.add(q["id"])

        tpl = q["templateID"]
        if tpl not in target_counts:
            raise ValueError(f"Unknown templateID {tpl}")
        counts[tpl] += 1

    for tpl, needed in target_counts.items():
        if counts[tpl] < needed:
            raise ValueError(f"Template {tpl} count {counts[tpl]} < required {needed}")
