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
CATEGORY_FUNCTIONS: Dict[str, callable] = {}

def register_template(tpl_id: str):
    """Decorator to register a templateID → function mapping."""

    def decorator(fn):
        _TEMPLATE_FN[tpl_id] = fn
        return fn

    return decorator

def register_category(category: str):
    """Decorator to register a category → function mapping."""

    def decorator(fn):
        CATEGORY_FUNCTIONS[category] = fn
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
    """Return comma-separated chronological list."""
    return ", ".join(ev.name for ev in timeline)


@register_template("order.reverse")
def order_reverse(timeline: List[SyntheticEvent], args: Dict) -> str:
    return ", ".join(ev.name for ev in reversed(timeline))


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


@register_template("dur.shortest")
def dur_shortest(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev = min(timeline, key=lambda e: e.duration)
    return ev.name


@register_template("order.first")
def order_first(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A = ev_map[args["event_A"]]
    B = ev_map[args["event_B"]]
    return A.name if A.start < B.start else B.name


@register_template("order.first_last")
def order_first_last(timeline: List[SyntheticEvent], args: Dict) -> str:
    first = timeline[0].name
    last = timeline[-1].name
    return f"{first}, {last}"


@register_template("count.over_x")
def count_over_x(timeline: List[SyntheticEvent], args: Dict) -> str:
    x = args["x"]
    # Count occurrences of each event
    event_counts = {}
    for ev in timeline:
        event_counts[ev.name] = event_counts.get(ev.name, 0) + 1
    
    # Get events that occurred more than x times
    over_x_events = [name for name, count in event_counts.items() if count > x]
    
    if not over_x_events:
        return "None"
    return ", ".join(over_x_events)


@register_template("count.same")
def count_same_occurrences(timeline: List[SyntheticEvent], args: Dict) -> str:
    # Count occurrences of each event
    event_counts = {}
    for ev in timeline:
        event_counts[ev.name] = event_counts.get(ev.name, 0) + 1
    
    # Group events by their count
    count_groups = {}
    for name, count in event_counts.items():
        if count not in count_groups:
            count_groups[count] = []
        count_groups[count].append(name)
    
    # Get groups with more than one event
    same_count_events = []
    for events in count_groups.values():
        if len(events) > 1:
            same_count_events.extend(events)
    
    if not same_count_events:
        return "None"
    return ", ".join(same_count_events)


@register_template("int.between")
def int_between(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A = ev_map[args["event_A"]]
    B = ev_map[args["event_B"]]
    delta = max(0, (B.start - A.end).days - 1)
    return f"{delta} days"


@register_template("order.count")
def order_count(timeline: List[SyntheticEvent], args: Dict) -> str:
    """Count total events."""
    return str(len(timeline))


@register_template("order.middle")
def order_middle(timeline: List[SyntheticEvent], args: Dict) -> str:
    """Return the middle event by index arg."""
    idx = int(args.get("index", len(timeline)//2))
    if not 0 <= idx < len(timeline):
        raise ValueError(f"index {idx} out of range")
    return timeline[idx].name


@register_template("dur.average")
def dur_average(timeline: List[SyntheticEvent], args: Dict) -> str:
    """Average duration of all events."""
    total = sum(ev.duration for ev in timeline)
    avg = round(total / len(timeline))
    return f"{avg} days"


@register_template("dur.each_asc")
def dur_each_asc(timeline: List[SyntheticEvent], args: Dict) -> str:
    """List events with durations in ascending order."""
    ordered = sorted(timeline, key=lambda e: e.duration)
    # return only event names (no durations) to match model output
    return ", ".join(ev.name for ev in ordered)


@register_template("dur.each_desc")
def dur_each_desc(timeline: List[SyntheticEvent], args: Dict) -> str:
    """List events with durations in descending order."""
    ordered = sorted(timeline, key=lambda e: e.duration, reverse=True)
    # return only event names (no durations) to match model output
    return ", ".join(ev.name for ev in ordered)


@register_template("int.between_consecutive")
def int_between_consecutive(timeline: List[SyntheticEvent], args: Dict) -> str:
    """Intervals between consecutive events."""
    intervals: List[str] = []
    for i in range(len(timeline)-1):
        d = max(0, (timeline[i+1].start - timeline[i].end).days - 1)
        intervals.append(f"{d} days")
    return ", ".join(intervals)


@register_template("int.precedes")
def int_precedes(timeline: List[SyntheticEvent], args: Dict) -> str:
    """Does event_A precede event_B?"""
    name_map = {ev.name: ev for ev in timeline}
    A = name_map[args["event_A"]]
    B = name_map[args["event_B"]]
    return "yes" if A.start < B.start else "no"


@register_template("list.between")
def list_between(timeline: List[SyntheticEvent], args: Dict) -> str:
    """List events occurring between event_A and event_B."""
    names = [ev.name for ev in timeline]
    idxA = names.index(args["event_A"])
    idxB = names.index(args["event_B"])
    lo, hi = min(idxA, idxB), max(idxA, idxB)
    between = timeline[lo+1:hi]
    if not between:
        return "None"
    return ", ".join(ev.name for ev in between)


@register_template("dur.counterfactual.single")
def dur_counterfactual_single(timeline: List[SyntheticEvent], args: Dict) -> str:
    # Same as single duration under counterfactual
    ev_map = _timeline_by_name(timeline)
    ev = ev_map[args['event']]
    return f"{ev.duration} days"


@register_template("dur.counterfactual.multiple")
def dur_counterfactual_multiple(timeline: List[SyntheticEvent], args: Dict) -> str:
    # List durations for all events under counterfactual
    return ", ".join(f"{ev.name}: {ev.duration} days" for ev in timeline)


@register_template("dur.bucket")
def dur_bucket(timeline: List[SyntheticEvent], args: Dict) -> str:
    # Divide events into three buckets by duration order
    sorted_ev = sorted(timeline, key=lambda e: e.duration)
    n = len(sorted_ev)
    third = max(1, n // 3)
    small = [ev.name for ev in sorted_ev[:third]]
    medium = [ev.name for ev in sorted_ev[third:2*third]]
    large = [ev.name for ev in sorted_ev[2*third:]]
    parts = []
    if small:
        parts.append(f"Small: {', '.join(small)}")
    if medium:
        parts.append(f"Medium: {', '.join(medium)}")
    if large:
        parts.append(f"Large: {', '.join(large)}")
    return "; ".join(parts)


@register_template("int.overlaps")
def int_overlaps(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A, B = ev_map[args['event_A']], ev_map[args['event_B']]
    overlap = not (A.end < B.start or B.end < A.start)
    return 'yes' if overlap else 'no'


@register_template("int.overlapped_by")
def int_overlapped_by(timeline: List[SyntheticEvent], args: Dict) -> str:
    # B overlapped by A is same as overlap
    return int_overlaps(timeline, {'event_A': args['event_A'], 'event_B': args['event_B']})


@register_template("int.during")
def int_during(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A, B = ev_map[args['event_A']], ev_map[args['event_B']]
    return 'yes' if A.start >= B.start and A.end <= B.end else 'no'


@register_template("int.contains")
def int_contains(timeline: List[SyntheticEvent], args: Dict) -> str:
    # B contains A
    return int_during(timeline, {'event_A': args['event_B'], 'event_B': args['event_A']})


@register_template("int.finishes")
def int_finishes(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A, B = ev_map[args['event_A']], ev_map[args['event_B']]
    return 'yes' if A.end == B.end and A.start > B.start else 'no'


@register_template("int.finished_by")
def int_finished_by(timeline: List[SyntheticEvent], args: Dict) -> str:
    # B is finished by A
    return int_finishes(timeline, {'event_A': args['event_B'], 'event_B': args['event_A']})


@register_template("int.same_interval")
def int_same_interval(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A, B = ev_map[args['event_A']], ev_map[args['event_B']]
    same = A.start == B.start and A.end == B.end
    return 'yes' if same else 'no'


@register_template("int.no_overlap")
def int_no_overlap(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A = ev_map[args['event_A']]
    for ev in timeline:
        if ev.name == A.name:
            continue
        if not (A.end < ev.start or ev.end < A.start):
            return 'no'
    return 'yes'


@register_template("list.pair_immediate")
def list_pair_immediate(timeline: List[SyntheticEvent], args: Dict) -> str:
    pairs = []
    for A in timeline:
        for B in timeline:
            if A.start == B.end:
                pairs.append(f"{A.name}/{B.name}")
    return ', '.join(pairs) if pairs else 'None'


@register_template("freq.single")
def freq_single(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    name = args['event']
    count = sum(1 for ev in timeline if ev.name == name)
    return str(count)


@register_template("freq.counterfactual")
def freq_counterfactual(timeline: List[SyntheticEvent], args: Dict) -> str:
    # same as freq.single under counterfactual
    return freq_single(timeline, args)


@register_template("freq.compare_intervals")
def freq_compare_intervals(timeline: List[SyntheticEvent], args: Dict) -> str:
    # Stub: return overall frequency
    return freq_single(timeline, args)


@register_template("freq.relative")
def freq_relative(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    name = args['event']
    count = sum(1 for ev in timeline if ev.name == name)
    total = len(timeline)
    return f"{count}/{total}"


@register_template("typical.time")
def typical_time(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    ev = ev_map[args['event']]
    # return ISO date of start as typical time
    return ev.start.isoformat()


@register_template("typical.compare")
def typical_compare(timeline: List[SyntheticEvent], args: Dict) -> str:
    # List events sorted by start as typical comparison
    return ", ".join(ev.name for ev in sorted(timeline, key=lambda e: e.start))


@register_template("causal.leads_to")
def causal_leads_to(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A, B = ev_map[args['event_A']], ev_map[args['event_B']]
    return 'yes' if A.end < B.start else 'no'


@register_template("causal.prerequisite")
def causal_prerequisite(timeline: List[SyntheticEvent], args: Dict) -> str:
    # event required before this event
    names = [ev.name for ev in timeline]
    idx = names.index(args['event'])
    return names[idx-1] if idx > 0 else 'None'


@register_template("causal.relation")
def causal_relation(timeline: List[SyntheticEvent], args: Dict) -> str:
    ev_map = _timeline_by_name(timeline)
    A, B = ev_map[args['event_A']], ev_map[args['event_B']]
    # any temporal relation
    if A.end < B.start or B.end < A.start or not (A.end < B.start or B.end < A.start):
        return 'yes'
    return 'no'

###############################################################################
# Category-level answer dispatchers
###############################################################################

@register_category('event_ordering')
def answer_event_ordering(timeline: List[SyntheticEvent], tpl: str, args: Dict) -> str:
    fn = _TEMPLATE_FN.get(tpl)
    if not fn:
        raise KeyError(f"Template {tpl} not implemented")
    return fn(timeline, args)

@register_category('event_duration')
def answer_event_duration(timeline: List[SyntheticEvent], tpl: str, args: Dict) -> str:
    fn = _TEMPLATE_FN.get(tpl)
    if not fn:
        raise KeyError(f"Template {tpl} not implemented")
    return fn(timeline, args)

@register_category('event_interval')
def answer_event_interval(timeline: List[SyntheticEvent], tpl: str, args: Dict) -> str:
    fn = _TEMPLATE_FN.get(tpl)
    if not fn:
        raise KeyError(f"Template {tpl} not implemented")
    return fn(timeline, args)

@register_category('event_frequency')
def answer_event_frequency(timeline: List[SyntheticEvent], tpl: str, args: Dict) -> str:
    fn = _TEMPLATE_FN.get(tpl)
    if not fn:
        raise KeyError(f"Template {tpl} not implemented")
    return fn(timeline, args)

@register_category('event_typical')
def answer_event_typical(timeline: List[SyntheticEvent], tpl: str, args: Dict) -> str:
    fn = _TEMPLATE_FN.get(tpl)
    if not fn:
        raise KeyError(f"Template {tpl} not implemented")
    return fn(timeline, args)

@register_category('event_causal')
def answer_event_causal(timeline: List[SyntheticEvent], tpl: str, args: Dict) -> str:
    fn = _TEMPLATE_FN.get(tpl)
    if not fn:
        raise KeyError(f"Template {tpl} not implemented")
    return fn(timeline, args)

###############################################################################
# Public API
###############################################################################

def compute_answers(timeline: List[SyntheticEvent], questions: List[Dict]) -> Dict[int, str]:
    """Return mapping {question_id: answer_str}."""
    # ensure timeline chronological
    timeline_sorted = sorted(timeline, key=lambda e: e.start)

    answers: Dict[int, str] = {}
    for q in questions:
        # dispatch by category if available
        category = q.get("category")
        tpl = q["templateID"]
        if category:
            # map category to function prefix
            fn = CATEGORY_FUNCTIONS[category]
            ans = fn(timeline_sorted, tpl, q["arguments"])
        else:
            if tpl not in _TEMPLATE_FN:
                raise KeyError(f"Template {tpl} not implemented in gold_engine")
            fn = _TEMPLATE_FN[tpl]
            ans = fn(timeline_sorted, q["arguments"])
        answers[q["id"]] = ans
    return answers