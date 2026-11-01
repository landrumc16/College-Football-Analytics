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
    # Preserve published forecasts across refreshes. Never reconstruct an old
    # forecast using a rating calculated after the game was played.
    history_path = output.with_name(f"pregame-{args.season}-history.json")
    history = json.loads(history_path.read_text()) if history_path.exists() else {}
    previous = json.loads(output.read_text()) if output.exists() else {}
    snapshot_data = json.loads(snapshot.read_text())
    completed_ids = {g["game_id"] for g in snapshot_data["games"] if g["completed"]}
    previous_retrieved = previous.get("retrieved_at")
    for prediction in previous.get("predictions", []):
        key = str(prediction["game_id"])
        if prediction["game_id"] in completed_ids and key not in history and previous_retrieved:
            history[key] = {**prediction, "forecast_recorded_at": previous_retrieved,
                            "source": "previously_published_forecast"}

    if len(roster) != 138:
        raise RuntimeError("Expected 138 frozen 2026 roster entries")
    roster_path = output.with_suffix(".roster.tmp.json")
    try:
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(json.dumps(roster), encoding="utf-8")
        result = run_snapshot(snapshot, roster_path, output)
        from .pipeline import build_performance_against_expectations
        result["performance"] = build_performance_against_expectations(
            snapshot_data, roster, history)
        output.write_text(json.dumps(result, indent=2) + "\\n", encoding="utf-8")
        history_path.write_text(json.dumps(history, indent=2) + "\\n", encoding="utf-8")
    finally:
        roster_path.unlink(missing_ok=True)
    print(json.dumps({"output": str(output), "summary": result["summary"]}))


if __name__ == "__main__":
    main()
