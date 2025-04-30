# event_library.py
"""Load and validate the curated real‑event dictionary.

The file *data/real_event_library.json* must be placed relative to this module.
Schema of each JSON entry
-------------------------
{
  "name" : str,                 # canonical event label
  "true_date" : "YYYY‑MM‑DD",   # historically correct single‑day date
  "theme" : str                 # e.g. "history", "tech", "sports" (optional)
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

__all__ = [
    "EventRecord",
    "load_events",
]


@dataclass(frozen=True, slots=True)
class EventRecord:
    """In‑memory representation of one real‑world event."""

    name: str
    true_date: date
    theme: Optional[str] = None

    @classmethod
    def from_json(cls, obj: dict) -> "EventRecord":
        try:
            d = datetime.strptime(obj["true_date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            raise ValueError(f"Bad or missing 'true_date' in record: {obj}")
        return cls(name=obj["name"].strip(), true_date=d, theme=obj.get("theme"))


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_JSON_PATH = MODULE_DIR / "data" / "real_event_library.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_events(theme: str | None = None, json_path: Path | str | None = None) -> List[EventRecord]:
    """Return all events, or those filtered by *theme*.

    Parameters
    ----------
    theme : str | None
        If provided, only events with .theme matching (case‑insensitive) are returned.
    json_path : Path | str | None
        Override the default location of the JSON file.
    """
    path = Path(json_path) if json_path else DEFAULT_JSON_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Event library JSON not found: {path}")

    with path.open("r", encoding="utf‑8") as fh:
        records_json = json.load(fh)

    events: List[EventRecord] = []
    for obj in records_json:
        try:
            rec = EventRecord.from_json(obj)
        except ValueError as e:
            # Skip invalid records but log
            print(f"[event_library] WARN {e}")
            continue
        if theme is None or (rec.theme and rec.theme.lower() == theme.lower()):
            events.append(rec)

    if not events:
        raise ValueError(f"No events found for theme='{theme}' in {path}")
    return events


# ---------------------------------------------------------------------------
# CLI helper for quick inspection
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, sys, textwrap

    parser = argparse.ArgumentParser(
        description="Inspect the curated event library.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--theme", help="Filter by theme tag (case‑insensitive)")
    parser.add_argument("--head", type=int, default=10, help="Show first N records (default 10)")
    args = parser.parse_args()

    try:
        evts = load_events(theme=args.theme)
    except Exception as exc:
        sys.exit(str(exc))

    print(f"Loaded {len(evts)} events\n")
    for rec in evts[: args.head]:
        print(textwrap.shorten(str(rec), width=120))
