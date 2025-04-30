# question_generator.py
"""Generate balanced question sets from a fact block using deterministic rules.

The generator produces JSON‑serialisable dicts with
    id, question, templateID, arguments
where *templateID* matches a deterministic answer function in *gold_engine.py*.

When no external calls are available, the module uses a **deterministic
rule‑driven generator** that simply walks through pre‑defined template
functions and instantiates arguments drawn from the supplied timeline.  This
ensures CI coverage without external calls.
"""
from __future__ import annotations

import itertools
import json
import random
from pathlib import Path
from typing import Dict, List, Sequence, Any

from tuple_builder import SyntheticEvent

# ---------------------------------------------------------------------------
# Template catalogue (must sync with gold_engine)
# ---------------------------------------------------------------------------
TEMPLATES = {
    "order.full": 1,
    "order.reverse": 1,
    "order.nth": 5,
    "dur.single": 5,
    "dur.longest": 1,
    "dur.shortest": 1,
    "order.first": 5,
    "order.first_last": 1,
    "count.over_x": 5,
    "count.same": 2,
    "int.between": 5,
    "order.count": 1,
    "order.middle": 1,
    "dur.average": 1,
    "dur.each_asc": 1,
    "dur.each_desc": 1,
    "int.between_consecutive": 1,
    "int.precedes": 5,
    "list.between": 5,
    'dur.counterfactual.single': 1,
    'dur.counterfactual.multiple': 1,
    'dur.bucket': 1,
    'int.overlaps': 1,
    'int.overlapped_by': 1,
    'int.during': 1,
    'int.contains': 1,
    'int.finishes': 1,
    'int.finished_by': 1,
    'int.same_interval': 1,
    'int.no_overlap': 1,
    'list.pair_immediate': 1,
    'freq.single': 1,
    'freq.counterfactual': 1,
    'freq.compare_intervals': 1,
    'freq.relative': 1,
    'typical.time': 1,
    'typical.compare': 1,
    'causal.leads_to': 1,
    'causal.prerequisite': 1,
    'causal.relation': 1,
}

# Category mapping for templates
TEMPLATE_CATEGORY = {
    'order.full': 'event_ordering',
    'order.reverse': 'event_ordering',
    'order.nth': 'event_ordering',
    'order.first': 'event_ordering',
    'order.first_last': 'event_ordering',
    'order.count': 'event_ordering',
    'order.middle': 'event_ordering',
    'dur.single': 'event_duration',
    'dur.longest': 'event_duration',
    'dur.shortest': 'event_duration',
    'dur.average': 'event_duration',
    'dur.each_asc': 'event_duration',
    'dur.each_desc': 'event_duration',
    'int.between': 'event_interval',
    'int.between_consecutive': 'event_interval',
    'int.precedes': 'event_interval',
    'list.between': 'event_interval',
    'count.over_x': 'event_frequency',
    'count.same': 'event_frequency',
    'dur.counterfactual.single': 'event_duration',
    'dur.counterfactual.multiple': 'event_duration',
    'dur.bucket': 'event_duration',
    'int.overlaps': 'event_interval',
    'int.overlapped_by': 'event_interval',
    'int.during': 'event_interval',
    'int.contains': 'event_interval',
    'int.finishes': 'event_interval',
    'int.finished_by': 'event_interval',
    'int.same_interval': 'event_interval',
    'int.no_overlap': 'event_interval',
    'list.pair_immediate': 'event_interval',
    'freq.single': 'event_frequency',
    'freq.counterfactual': 'event_frequency',
    'freq.compare_intervals': 'event_frequency',
    'freq.relative': 'event_frequency',
    'typical.time': 'event_typical',
    'typical.compare': 'event_typical',
    'causal.leads_to': 'event_causal',
    'causal.prerequisite': 'event_causal',
    'causal.relation': 'event_causal',
}

# Question text variations per template
QUESTION_VARIATIONS = {
    "order.full": [
        "List the events in chronological order.",
        "Provide the events from earliest to latest.",
        "What is the chronological sequence of events?",
    ],
    "order.reverse": [
        "List the events in reverse chronological order.",
        "Provide the events from latest to earliest.",
        "What is the reverse order of the events?",
    ],
    "order.nth": [
        "What is the {n}{suffix} event chronologically?", 
        "Which event is the {n}{suffix} in the sequence?", 
        "Tell me the {n}{suffix} event in order.",
        "Identify the {n}{suffix} event chronologically.",
        "Which event ranks {n}{suffix} in the timeline?",
    ],
    "dur.single": [
        "How long did {event} last?",
        "What was the duration of {event}?",
        "For how many days did {event} occur?",
        "{event} lasted how many days?",
        "Duration of {event}?",
    ],
    "dur.longest": [
        "Which event lasted the longest?",
        "Identify the longest-lasting event.",
        "What event had the maximum duration?",
    ],
    "dur.shortest": [
        "Which event lasted the shortest?",
        "Identify the shortest-lasting event.",
        "What event had the minimum duration?",
    ],
    "order.first": [
        "Which of {event_A} and {event_B} occurred first?",
        "Between {event_A} and {event_B}, which happened earlier?",
        "Which event came first: {event_A} or {event_B}?",
        "Did {event_A} or {event_B} occur first?",
        "What occurred earlier, {event_A} or {event_B}?",
    ],
    "order.first_last": [
        "What is the first and last event?",
        "Identify the earliest and latest events.",
        "Which events are at the start and end of the timeline?",
    ],
    "count.over_x": [
        "Which events occurred more than {x} times?",
        "List events with frequency > {x}.",
        "Name events that happened over {x} times.",
        "Which items exceed {x} occurrences?",
        "Events occurring more than {x} times?",
    ],
    "count.same": [
        "Which events have the same occurrence count?",
        "List events that occurred equally often.",
        "Identify events sharing the same frequency.",
    ],
    "int.between": [
        "What is the duration between the end of {event_A} and the start of {event_B}?",
        "How many days passed between {event_A} ending and {event_B} starting?",
        "Calculate days between {event_A} and {event_B}.",
        "Days between end of {event_A} and start of {event_B}?",
        "Interval between {event_A} end and {event_B} start?",
    ],
    "order.count": [
        "How many events are there?",
        "Total number of events?",
        "Count of events in the timeline?",
    ],
    "order.middle": [
        "Which event is in the middle of the sequence?",
        "What event sits at the midpoint of the timeline?",
        "Identify the middle event chronologically.",
    ],
    "dur.average": [
        "What is the average duration of all events?",
        "On average, how many days did events last?",
        "Compute the mean event duration.",
    ],
    "dur.each_asc": [
        "List events with durations in ascending order.",
        "Which events, sorted by increasing duration, occurred?",
        "Order the events by shortest to longest duration.",
    ],
    "dur.each_desc": [
        "List events with durations in descending order.",
        "Which events, sorted by decreasing duration, occurred?",
        "Order the events by longest to shortest duration.",
    ],
    "int.between_consecutive": [
        "What are the time intervals between consecutive events?",
        "List the days between each pair of consecutive events.",
        "How many days separate each successive event?",
    ],
    "int.precedes": [
        "Does {event_A} precede {event_B}?",
        "Does {event_A} come before {event_B}?",
        "Is {event_A} earlier than {event_B}?",
        "Does {event_A} occur before {event_B}?",
        "Which comes first, {event_A} or {event_B}?",
    ],
    "list.between": [
        "List the events that occur between {event_A} and {event_B}.",
        "Which events happened between {event_A} and {event_B}?",
        "Name events occurring between {event_A} and {event_B}.",
        "What events fall between {event_A} and {event_B}?",
        "Identify events between {event_A} and {event_B}.",
    ],
    'dur.counterfactual.single': [
        'What would be the duration of {event} under the counterfactual scenario?',
    ],
    'dur.counterfactual.multiple': [
        'What are the durations of multiple events given counterfactuals?',
    ],
    'dur.bucket': [
        'Categorize events into buckets: Small, Medium, Large based on duration.',
    ],
    'int.overlaps': [
        'Does {event_A} overlap with {event_B}?',
    ],
    'int.overlapped_by': [
        'Is {event_B} overlapped by {event_A}?',
    ],
    'int.during': [
        'Does {event_A} occur during {event_B}?',
    ],
    'int.contains': [
        'Does {event_B} contain {event_A}?',
    ],
    'int.finishes': [
        'Does {event_A} finish {event_B}?',
    ],
    'int.finished_by': [
        'Is {event_B} finished by {event_A}?',
    ],
    'int.same_interval': [
        'Are {event_A} and {event_B} in the same interval?',
    ],
    'int.no_overlap': [
        'Does {event_A} have no overlap with any other event?',
    ],
    'list.pair_immediate': [
        'List pairs where {event_A} starts as soon as {event_B} ends.',
    ],
    'freq.single': [
        'What is the frequency of {event} in the timeline?',
    ],
    'freq.counterfactual': [
        'What is the frequency of {event} given the counterfactual?',
    ],
    'freq.compare_intervals': [
        'Compare frequency of {event} across intervals.',
    ],
    'freq.relative': [
        'What is the relative frequency of {event}?',
    ],
    'typical.time': [
        'What is the typical time of {event}?',
    ],
    'typical.compare': [
        'Compare typical times between event types.',
    ],
    'causal.leads_to': [
        'Did the occurrence of {event_A} lead to {event_B}?',
    ],
    'causal.prerequisite': [
        'What should have occurred for {event} to take place?',
    ],
    'causal.relation': [
        'Is there any relation between {event_A} and {event_B}?',
    ],
}

# ---------------------------------------------------------------------------
# Helper / deterministic generator
# ---------------------------------------------------------------------------

import string

def _deterministic_questions(timeline: List[SyntheticEvent], max_q: int = None) -> List[Dict]:
    """Return a small fixed set of deterministic questions for CI/offline use."""
    qs: List[Dict] = []
    qid = 1
    formatter = string.Formatter()
    for tpl, freq in TEMPLATES.items():
        for _ in range(freq):
            template_text = random.choice(QUESTION_VARIATIONS.get(tpl, []))
            # extract fields
            args: Dict[str, Any] = {}
            for _, field_name, _, _ in formatter.parse(template_text):
                if not field_name:
                    continue
                if field_name == 'event':
                    args['event'] = random.choice(timeline).name
                elif field_name == 'event_A':
                    a, b = random.sample(timeline, 2)
                    args['event_A'], args['event_B'] = a.name, b.name
                elif field_name == 'event_B':
                    continue  # already set with event_A
                elif field_name == 'n':
                    args['n'] = random.randint(1, len(timeline))
                elif field_name == 'suffix':
                    args['suffix'] = _ordinal_suffix(args.get('n', 1))
                elif field_name == 'x':
                    args['x'] = random.randint(1, 5)
                else:
                    args[field_name] = None
            q_text = template_text.format(**args)
            qs.append({
                'id': qid,
                'templateID': tpl,
                'question': q_text,
                'arguments': args
            })
            qid += 1
    # attach categories
    for q in qs:
        q['category'] = TEMPLATE_CATEGORY.get(q['templateID'])
    return qs


def _ordinal_suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

# ---------------------------------------------------------------------------
# Deterministic generator wrapper
# ---------------------------------------------------------------------------

def generate_questions(
    fact_block: str,
    timeline: Sequence[SyntheticEvent],
) -> List[Dict]:
    """Return list of structured question dicts."""
    # Always use deterministic generator
    return _deterministic_questions(list(timeline))