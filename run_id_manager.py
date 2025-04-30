# run_id_manager.py
from pathlib import Path

_COUNTER_FILE = Path("runs/run_counter.txt")

def next_run_id() -> str:
    """Return the next sequential ID: run_0001, run_0002, …"""
    _COUNTER_FILE.parent.mkdir(exist_ok=True)
    if _COUNTER_FILE.exists():
        n = int(_COUNTER_FILE.read_text().strip()) + 1
    else:
        n = 1
    _COUNTER_FILE.write_text(str(n))
    return f"run_{n:04d}"
