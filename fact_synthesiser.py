# fact_synthesiser.py
"""Convert synthetic event tuples into natural‑language fact sentences.

Two surface variants are produced:

* **ABS**  – absolute dates (ISO‑8601) for every event.
* **REL**  – the first event uses an absolute date; all subsequent events are
            described *relatively* to their immediate predecessor using a
            synonym randomly drawn from the `TEMPORAL_SYNONYMS` table.

A lightweight wrapper around an external LLM (e.g., GPT‑4o) is provided.  If an
LLM key is unavailable, the module can fall back to a deterministic *template
renderer* for unit‑testing (so CI does not require API calls).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from random import Random
from typing import List, Sequence

# External deps kept optional to allow import without credentials
try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

from tuple_builder import SyntheticEvent

__all__ = [
    "synthesize_facts",
    "LLMClient",
]

###############################################################################
# Temporal synonym table (can be extended)
###############################################################################
TEMPORAL_SYNONYMS = {
    "after": [
        "after",
        "following",
        "subsequently",
        "soon after",
        "later",
    ],
    "before": [
        "before",
        "prior to",
        "preceding",
        "earlier than",
    ],
    "immediately": [
        "immediately after",
        "right after",
        "as soon as",
    ],
}

###############################################################################
# Fallback deterministic templates (no LLM) – good for tests & CI
###############################################################################

def _abs_sentence(ev: SyntheticEvent) -> str:
    return f"{ev.name} started on {ev.start.isoformat()} and ended on {ev.end.isoformat()}."


def _rel_sentence(prev: SyntheticEvent, curr: SyntheticEvent, rng: Random) -> str:
    delta = (curr.start - prev.end).days  # could be negative if deliberate shuffle

    if delta == 1:
        phrase = rng.choice(TEMPORAL_SYNONYMS["immediately"])
        return f"{curr.name} began {phrase} {prev.name} and lasted {curr.duration} days."

    direction = "after" if delta > 0 else "before"
    synonym = rng.choice(TEMPORAL_SYNONYMS[direction])
    abs_delta = abs(delta)
    unit = "day" if abs_delta == 1 else "days"
    return (
        f"{curr.name} began {abs_delta} {unit} {synonym} {prev.name} "
        f"and lasted {curr.duration} days."
    )

###############################################################################
# LLM wrapper (optional)
###############################################################################

@dataclass
class LLMClient:
    """Thin wrapper around OpenAI client with graceful degradation."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    openai_api_key: str | None = None

    def __post_init__(self):
        if OpenAI is None:
            raise RuntimeError("openai package is not installed; install or set use_llm=False")
        self.cli = OpenAI(api_key=self.openai_api_key)

    def render(self, prompt: str) -> str:
        resp = self.cli.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return resp.choices[0].message.content.strip()

###############################################################################
# Main synthesiser function
###############################################################################

def synthesize_facts(
    tuples: Sequence[Sequence[SyntheticEvent]],
    *,
    variant: str = "ABS",
    rng_seed: int | None = None,
    use_llm: bool = False,
    llm_client: LLMClient | None = None,
) -> List[str]:
    """Return list of fact sentences for the given variant.

    Variant rules
    -------------
    * **ABS** – each event becomes its own absolute sentence.
    * **REL** – first event: absolute; rest: relative to previous event.

    If *use_llm* is False, deterministic templates are used.
    """

    rng = Random(rng_seed)
    sentences: List[str] = []

    if variant not in {"ABS", "REL"}:
        raise ValueError("variant must be 'ABS' or 'REL'")

    # Flatten tuple list to a global timeline order (synthetic timeline is chronological)
    timeline = [ev for tup in tuples for ev in tup]
    timeline.sort(key=lambda e: e.start)

    for idx, ev in enumerate(timeline):
        if variant == "ABS" or idx == 0:
            if use_llm:
                prompt = _build_abs_prompt(ev)
                sentence = llm_client.render(prompt) if llm_client else _abs_sentence(ev)
            else:
                sentence = _abs_sentence(ev)
            sentences.append(sentence)
            continue

        # variant == REL and idx > 0
        prev = timeline[idx - 1]
        if use_llm:
            prompt = _build_rel_prompt(prev, ev)
            sentence = llm_client.render(prompt) if llm_client else _rel_sentence(prev, ev, rng)
        else:
            sentence = _rel_sentence(prev, ev, rng)
        sentences.append(sentence)

    return sentences


###############################################################################
# Helper – build prompts when using LLM
###############################################################################

def _build_abs_prompt(ev: SyntheticEvent) -> str:
    return (
        "Convert the structured data into a single English sentence. "
        "Use ISO‑8601 dates.\n" +
        f"EVENT_NAME: {ev.name}\nSTART: {ev.start.isoformat()}\nEND: {ev.end.isoformat()}"
    )


def _build_rel_prompt(prev: SyntheticEvent, curr: SyntheticEvent) -> str:
    delta = (curr.start - prev.end).days
    direction = "after" if delta > 0 else "before"
    abs_delta = abs(delta)
    return (
        "Write one sentence describing the timing of CURR relative to PREV. "
        "Use natural temporal language (e.g., 'seven days after'). "
        "Mention the duration explicitly in days.\n" +
        f"PREV_NAME: {prev.name}\nCURR_NAME: {curr.name}\nDELTA_DAYS: {delta}\nCURR_DURATION: {curr.duration}"
    )
