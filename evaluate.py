import csv
import subprocess
import sys
import re
from pathlib import Path

# Updated model variations: use the exact "llama-3.3-70b-versatile" ID for Groq
MODELS = [
    ('groq:llama-3.3-70b-versatile', 'llama'),
    ('gemini:gemini-2.0-flash', 'gemini'),
]
VARIATIONS = [11, 15, 21]
RUNS_PER = 4

# Run runs for each model across event-count variations
def run_variation(label: str, model_str: str) -> None:
    cwd = Path(__file__).parent
    runs_dir = cwd / 'runs'
    consolidated = runs_dir / f"{label}_consolidated.csv"
    with consolidated.open('w', newline='', encoding='utf-8') as cons:
        writer = None
        for ev_count in VARIATIONS:
            for i in range(1, RUNS_PER + 1):
                print(f"Starting {label} run (events={ev_count}) {i}/{RUNS_PER}...")
                cmd = [
                    sys.executable, 'main.py',
                    '--model', model_str,
                    '--seed', str(i),
                    '--theme', 'all',
                    '--max_events', str(ev_count),
                    '--shuffle_abs',
                    '--shuffle_rel',
                ]
                try:
                    cp = subprocess.run(
                        cmd,
                        cwd=cwd,
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minutes max per run
                    )
                except subprocess.TimeoutExpired:
                    print(f"Run timed out for cmd: {cmd}")
                    continue

                if cp.returncode != 0:
                    print(f"Subprocess {cmd!r} exited {cp.returncode}:")
                    print(cp.stdout)
                    print(cp.stderr)
                    continue

                out = cp.stdout + cp.stderr
                m = re.search(r"Run (run_\d+) complete", out)
                if not m:
                    print(f"Could not parse run_id from output:\n{out}")
                    continue
                run_id = m.group(1)
                orig = runs_dir / f"results_{run_id}.csv"
                dest = runs_dir / f"{label}_{ev_count}_{run_id}.csv"
                orig.rename(dest)

                # Append to consolidated
                with dest.open(newline='', encoding='utf-8') as fh:
                    rows = list(csv.reader(fh))
                if writer is None:
                    writer = csv.writer(cons)
                    writer.writerow(rows[0] + ['model', 'max_events'])
                for row in rows[1:]:
                    writer.writerow(row + [label, ev_count])
                print(f"Completed {label} events={ev_count} run {run_id} → {dest.name}")
    print(f"Consolidated results for {label} into {consolidated}")


def main() -> None:
    for model_str, label in MODELS:
        run_variation(label, model_str)


if __name__ == '__main__':
    main()
