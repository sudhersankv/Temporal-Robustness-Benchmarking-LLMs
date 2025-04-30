# fact_synthesiser.py
"""Convert synthetic event tuples into natural-language fact sentences.

Variants
--------
* ABS  – produce absolute-date facts in one of three formats:
        - sentence: full sentences.
        - inline: semicolon-separated list of "Name" (start; end).
        - list: bulleted list.
* REL  – first event absolute; remaining events described relatively with varied templates,
        including weeks-based phrasing, overlap cases, and optional approximate modifiers.
"""
from __future__ import annotations

from random import Random
from typing import List, Sequence

from tuple_builder import SyntheticEvent

__all__ = ["synthesize_facts"]

###############################################################################
# Template banks
###############################################################################
_POS_TEMPLATES = [
    '"{curr}" kicked off {d} days after "{prev}" wrapped up and lasted {dur} days.',
    'Following "{prev}" by {d} days, "{curr}" spanned {dur} days.',
    '"{curr}" was initiated {d} days post "{prev}" and continued for {dur} days.',
    'It took {d} days after "{prev}" ended for "{curr}" to commence; it ran {dur} days.',
    '"{curr}" came {d} days after "{prev}", lasting {dur} days.',
    '{d} days after the conclusion of "{prev}", "{curr}" began and persisted for {dur} days.',
    'The interval of {d} days between "{prev}" and "{curr}" marked the start of another {dur}-day chapter.',
    'Exactly {d} days elapsed between "{prev}" and the start of "{curr}", which endured {dur} days.',
    '"{curr}" surfaced {d} days after "{prev}", occupying the timeline for {dur} days.',
    '"{curr}" followed "{prev}" by {d} days and endured {dur} days.',
]

###############################################################################
# Sentence generators
###############################################################################
def _abs_sentence(ev: SyntheticEvent) -> str:
    return (
        f'The event "{ev.name}" started on {ev.start.isoformat()} '
        f'and ended on {ev.end.isoformat()}.'
    )

def _rel_sentence(prev: SyntheticEvent, curr: SyntheticEvent, rng: Random) -> str:
    """Generate varied relative-time sentence using POS_TEMPLATES."""
    delta = (curr.start - prev.end).days
    dur = curr.duration
    tpl = rng.choice(_POS_TEMPLATES)
    return tpl.format(curr=curr.name, prev=prev.name, d=delta, dur=dur)

###############################################################################
# Public API
###############################################################################
def synthesize_facts(
    events: Sequence[SyntheticEvent],
    *,
    variant: str = "ABS",
    rng_seed: int | None = None,
    shuffle_rel: bool = False,
    abs_format: str = "sentence",
    shuffle_abs: bool = True,
) -> List[str]:
    """Return list of fact sentences for the chosen variant.

    Parameters
    ----------
    events        : flat list of SyntheticEvent objects
    variant      : 'ABS' or 'REL'
    rng_seed     : deterministic seed for reproducibility
    shuffle_rel  : if True and variant == 'REL', randomize narrative order
    abs_format   : 'sentence', 'inline', or 'list'
    shuffle_abs  : if True and variant == 'ABS', randomize event order
    """
    if variant not in {"ABS", "REL"}:
        raise ValueError("variant must be 'ABS' or 'REL'")

    rng = Random(rng_seed)

    # Sort the flat list of synthetic events chronologically
    timeline = sorted(events, key=lambda e: e.start)

    if variant == "ABS":
        # optional shuffle of event order
        ev_list = list(timeline)
        if shuffle_abs:
            rng.shuffle(ev_list)
        # inline and list use combined items
        if abs_format == "inline":
            items = [f'"{ev.name}" (start: {ev.start.isoformat()}; end: {ev.end.isoformat()})' for ev in ev_list]
            return ["; ".join(items)]
        if abs_format == "list":
            items = [f'"{ev.name}" (start: {ev.start.isoformat()}; end: {ev.end.isoformat()})' for ev in ev_list]
            return [f"- {it}" for it in items]
        # sentence variant: one sentence per event
        return [_abs_sentence(ev) for ev in ev_list]

    # REL variant
    if variant == "REL":
        # pair each event with its immediate predecessor
        pairs = list(zip(timeline, timeline[1:]))
        # shuffle the pairs if requested (rel facts order)
        if shuffle_rel:
            rng.shuffle(pairs)
        # absolute sentence for first event
        sentences = [_abs_sentence(timeline[0])]
        # generate relative sentences for each pair
        for prev, curr in pairs:
            sentences.append(_rel_sentence(prev, curr, rng))
        return sentences
    print(sentences)
    raise RuntimeError("Unhandled variant in synthesize_facts")
