# gold_engine.py
"""Deterministic gold‑answer calculator for every supported template.

The module exposes:

    compute_answers(timeline, questions) -> {id: answer_str}

* `timeline` is the **chronologically sorted** list of `SyntheticEvent` objects
  corresponding to the fact set.
* Each *question* dict must include `id`, `templateID`, and `arguments`.

All template implementation functions **return a plain string** (no period).
"""
from __future__ import annotations

from typing import Dict, List

from tuple_builder import SyntheticEvent

__all__ = [
    "compute_answers",
]

###############################################################################
# Template function registry
###############################################################################

_TEMPLATE_FN: Dict[str, callable] = {}


def register_template(tpl_id: str):
    """Decorator to register a templateID → function mapping."""

    def decorator(fn):
        _TEMPLATE_FN[tpl_id] = fn
        return fn

    return decorator

###############################################################################
# Utility helpers
###############################################################################

def _timeline_by_name(timeline: List[SyntheticEvent]) -> Dict[str, SyntheticEvent]:
    return {ev.name: ev for ev in timeline}

###############################################################################
# Template implementations
###############################################################################

@register_template("order.full")
def order_full(timeline: List[SyntheticEvent], args: Dict) -> str:  # noqa: D401
    """Return arrow‑joined chronological list."""
    return " -> ".join(ev.name for ev in timeline)


@register_template("order.reverse")
def order_reverse(timeline: List[SyntheticEvent], args: Dict) -> str:
    return " -> ".join(ev.name for ev in reversed(timeline))


@register_template("order.nth")
def order_nth(timeline: List[SyntheticEvent], args: Dict) -> str:
    n = int(args["n"])
    if not 1 <= n <= len(timeline):
        raise ValueError(f"n={n} out of range for timeline length {len(timeline)}")
    return timeline[n - 1].name


@register_template("dur.single")
def dur_single(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    ev = ev_map[args["event"]]
    return f"{ev.duration} days"


@register_template("dur.longest")
def dur_longest(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev = max(timeline, key=lambda e: e.duration)
    return ev.name


@register_template("int.between")
def int_between(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A = ev_map[args["event_A"]]
    B = ev_map[args["event_B"]]
    delta = (B.start - A.end).days - 1
    return f"{delta} days"

###############################################################################
# Public API
###############################################################################

def compute_answers(timeline: List[SyntheticEvent], questions: List[Dict]) -> Dict[int, str]:
    """Return mapping {question_id: answer_str}."""
    # ensure timeline chronological
    timeline_sorted = sorted(timeline, key=lambda e: e.start)

    answers: Dict[int, str] = {}
    for q in questions:
        tpl = q["templateID"]
        if tpl not in _TEMPLATE_FN:
            raise KeyError(f"Template {tpl} not implemented in gold_engine")
        fn = _TEMPLATE_FN[tpl]
        ans = fn(timeline_sorted, q["arguments"])
        answers[q["id"]] = ans
    return answers
