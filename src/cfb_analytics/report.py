"""Generate a complete season report from a refreshed CFBD snapshot.

Until season-specific roster/prior ingestion is implemented, only the frozen
2026 baseline is supported. Refuse other seasons rather than silently
using incorrect priors.
"""
import argparse
import json
from pathlib import Path
from .parity import load_baseline
from .pipeline import run_snapshot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.season != 2026:
        parser.error("Only 2026 is supported until season-specific priors are available")
    snapshot = args.snapshot or Path("data") / f"cfbd-{args.season}-games.json"
    output = args.output or Path("data") / f"season-{args.season}-report.json"
    roster, _ = load_baseline()
    if len(roster) != 138:
        raise RuntimeError("Expected 138 frozen 2026 roster entries")
    roster_path = output.with_suffix(".roster.tmp.json")
    try:
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(json.dumps(roster), encoding="utf-8")
        result = run_snapshot(snapshot, roster_path, output)
    finally:
        roster_path.unlink(missing_ok=True)
    print(json.dumps({"output": str(output), "summary": result["summary"]}))


if __name__ == "__main__":
    main()
