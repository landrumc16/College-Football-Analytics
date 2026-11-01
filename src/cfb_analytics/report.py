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


from datetime import datetime, timezone


def parse_utc(value):
    """Return an aware UTC timestamp or None; never guess a missing timezone."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def verified_pregame(publication_time, kickoff_time):
    published = parse_utc(publication_time)
    kickoff = parse_utc(kickoff_time)
    return published is not None and kickoff is not None and published < kickoff


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
    completed_games = {g["game_id"]: g for g in snapshot_data["games"] if g["completed"]}
    previous_retrieved = previous.get("retrieved_at")
    previous_generated = previous.get("generated_at")
    # Published predictions are the authoritative set of games forecast while pending.
    # The school schedule is FBS-filtered and can omit otherwise valid forecasts.
    previous_pending = {p["game_id"] for p in previous.get("predictions", [])}
    eligible_fbs = {team["name"] for team in roster}
    aliases = {"Miami": "Miami (FL)", "App State": "Appalachian State",
               "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}
    for prediction in previous.get("predictions", []):
        key = str(prediction["game_id"])
        if (prediction["game_id"] in completed_games and key not in history
                and prediction["game_id"] in previous_pending
                and prediction.get("home") in eligible_fbs
                and prediction.get("away") in eligible_fbs):
            game = completed_games[prediction["game_id"]]
            if not verified_pregame(previous_retrieved, game.get("start_date")):
                continue
            # A snapshot's retrieval time does not prove when its forecast
            # was computed. Only archive reports with an explicit generation
            # timestamp strictly preceding kickoff.
            if not verified_pregame(previous_generated, game.get("start_date")):
                continue
            if (prediction["home"] != aliases.get(game["home"], game["home"]) or
                    prediction["away"] != aliases.get(game["away"], game["away"])):
                continue
            history[key] = {**prediction, "forecast_recorded_at": previous_generated,
                            "source_retrieved_at": previous_retrieved,
                            "source": "previously_published_forecast"}

    if len(roster) != 138:
        raise RuntimeError("Expected 138 frozen 2026 roster entries")
    roster_path = output.with_suffix(".roster.tmp.json")
    try:
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(json.dumps(roster), encoding="utf-8")
        result = run_snapshot(snapshot, roster_path, output)
        from .pipeline import build_performance_against_expectations, build_prediction_accuracy
        from datetime import datetime, timezone
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        result["performance"] = build_performance_against_expectations(
            snapshot_data, roster, history)
        # Measure the FBS model only on games between schools in its rating universe.
        # Preserve other archived forecasts, but never present their results as FBS accuracy.
        fbs_teams = {team['name'] for team in roster}
        result["prediction_accuracy"] = build_prediction_accuracy(
            snapshot_data, history, eligible_teams=fbs_teams)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        history_path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    finally:
        roster_path.unlink(missing_ok=True)
    print(json.dumps({"output": str(output), "summary": result["summary"]}))


if __name__ == "__main__":
    main()
