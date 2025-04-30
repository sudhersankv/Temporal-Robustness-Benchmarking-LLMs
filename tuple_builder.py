# tuple_builder.py
"""Construct pair‑ or triplet‑based synthetic timelines using *real* event names.

The synthetic timeline assigns **fake** start / end dates while preserving a
strict global chronology (unless intentionally shuffled *within* a tuple to
generate an ordering conflict).

Typical use:

```python
from event_library import load_events
from tuple_builder import TupleBuilder

events = load_events("history")          # real names, true dates ignored here
builder = TupleBuilder(rng_seed=42)
triplets = builder.build(events, tuple_size=3,
                         total_tuples=10,  # 30 events total
                         wrong_order_prob=0.25)
# ⇒ list[list[SyntheticEvent]] length 10
```
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Sequence

from event_library import EventRecord

__all__ = [
    "SyntheticEvent",
    "TupleBuilder",
]

# ---------------------------------------------------------------------------
# Configuration defaults (can be overridden per instance)
# ---------------------------------------------------------------------------
MIN_GAP_DAYS = 1
MAX_GAP_DAYS = 20
MIN_DUR_DAYS = 1
MAX_DUR_DAYS = 30
BASE_START = date(2000, 1, 1)  # anchor for synthetic timelines


@dataclass(slots=True, frozen=True)
class SyntheticEvent:
    """Event name plus synthetic timeline fields."""

    name: str
    start: date
    end: date
    # keep reference to original for potential audits
    true_date: date | None = None

    @property
    def duration(self) -> int:  # inclusive days
        return (self.end - self.start).days + 1


# ---------------------------------------------------------------------------
# Tuple Builder
# ---------------------------------------------------------------------------
class TupleBuilder:
    """Assign synthetic dates to sampled events, returning pairs / triplets.

    Parameters
    ----------
    rng_seed : int | None
        Seed for determinism.
    min_gap, max_gap : int
        Gap in days between consecutive events **across the global timeline**.
    min_dur, max_dur : int
        Duration range (inclusive) for each event.
    base_start : date
        Earliest possible synthetic start date.
    max_overlap : int
        Maximum overlap between consecutive events.
    jitter : int
        Random jitter to apply to event dates.
    """

    def __init__(
        self,
        rng_seed: int | None = None,
        *,
        min_gap: int = MIN_GAP_DAYS,
        max_gap: int = MAX_GAP_DAYS,
        max_overlap: int = 0,
        jitter: int = 0,
        min_dur: int = MIN_DUR_DAYS,
        max_dur: int = MAX_DUR_DAYS,
        base_start: date = BASE_START,
    ) -> None:
        self.rng = random.Random(rng_seed)
        self.min_gap = min_gap
        self.max_gap = max_gap
        if max_overlap < 0:
            raise ValueError("max_overlap must be >= 0")
        self.max_overlap = max_overlap
        if jitter < 0:
            raise ValueError("jitter must be >= 0")
        self.jitter = jitter
        self.min_dur = min_dur
        self.max_dur = max_dur
        self.base_start = base_start

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------
    def build(
        self,
        source_events: Sequence[EventRecord],
        *,
        tuple_size: int = 1,
        total_tuples: int = 10,
        wrong_order_prob: float = 0.0,
    ) -> List[List[SyntheticEvent]]:
        """Return list of tuples (pairs/triplets) with synthetic dates.

        Notes
        -----
        * Global timeline is always chronological.
        * **Within** a tuple, events may be shuffled with probability
          *wrong_order_prob* to create local order conflicts.
        """
        if tuple_size not in (1, 2, 3):
            raise ValueError("tuple_size must be 1, 2, or 3")
        needed = tuple_size * total_tuples
        if needed > len(source_events):
            raise ValueError(
                f"Not enough source events ({len(source_events)}) for requested "
                f"{total_tuples}×{tuple_size} tuples."
            )

        sampled = self.rng.sample(list(source_events), k=needed)
        cursor = self.base_start + timedelta(days=self.rng.randint(0, 365))
        tuples: List[List[SyntheticEvent]] = []

        for i in range(total_tuples):
            subevents: List[SyntheticEvent] = []
            for j in range(tuple_size):
                ev = sampled[i * tuple_size + j]
                duration = self.rng.randint(self.min_dur, self.max_dur)
                start = cursor
                end = start + timedelta(days=duration - 1)
                # apply jitter to both start and end
                if self.jitter:
                    joff = self.rng.randint(-self.jitter, self.jitter)
                    start = start + timedelta(days=joff)
                    end = end + timedelta(days=joff)
                    # ensure start not before base_start
                    if start < self.base_start:
                        start = self.base_start
                        end = start + timedelta(days=duration - 1)
                synthetic = SyntheticEvent(ev.name, start, end, true_date=ev.true_date)
                subevents.append(synthetic)
                # advance cursor for next event (global)
                if self.max_overlap:
                    gap = self.rng.randint(-self.max_overlap, self.max_gap)
                else:
                    gap = self.rng.randint(self.min_gap, self.max_gap)
                cursor = end + timedelta(days=gap)

            # possibly shuffle ordering **within** tuple to create wrong chronology
            if self.rng.random() < wrong_order_prob:
                self.rng.shuffle(subevents)
            tuples.append(subevents)

        return tuples


# ---------------------------------------------------------------------------
# Quick smoke‑test CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from event_library import load_events

    evs = load_events()
    tb = TupleBuilder(rng_seed=123)
    triplets = tb.build(evs, tuple_size=3, total_tuples=4, wrong_order_prob=0.5)

    for idx, t in enumerate(triplets, 1):
        print(f"\nTuple {idx}")
        for e in t:
            print(f"  {e.name:<30} {e.start} – {e.end}  (dur {e.duration}d)")
