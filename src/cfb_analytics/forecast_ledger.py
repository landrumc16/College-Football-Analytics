"""Immutable first-observed pregame forecasts for Version 3.1.

The source retrieval and report generation times must both precede kickoff.
This ledger does not backfill historical predictions.
"""
from datetime import datetime, timezone
import math


ALIASES = {"Miami": "Miami (FL)", "App State": "Appalachian State",
           "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}


def aware_utc(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except ValueError:
        return None


def archive_pending(history, report, snapshot):
    """Return an updated ledger without mutating existing first observations."""
    generated = aware_utc(report.get("generated_at"))
    retrieved = aware_utc(report.get("retrieved_at"))
    if generated is None or retrieved is None or retrieved > generated or generated > datetime.now(timezone.utc):
        return dict(history)
    games = {str(g["game_id"]): g for g in snapshot.get("games", [])}
    result = dict(history)
    model_id = report.get("model_metadata", {}).get("model_id")
    if not model_id:
        return result
    for prediction in report.get("predictions", []):
        key = str(prediction.get("game_id"))
        if key in result:
            continue
        game = games.get(key)
        if not game or game.get("completed"):
            continue
        kickoff = aware_utc(game.get("start_date"))
        if kickoff is None or not (retrieved < kickoff and generated < kickoff):
            continue
        home = ALIASES.get(game.get("home"), game.get("home"))
        away = ALIASES.get(game.get("away"), game.get("away"))
        if prediction.get("home") != home or prediction.get("away") != away:
            continue
        probability = prediction.get("home_win_probability")
        if (isinstance(probability, bool) or not isinstance(probability, (int, float))
                or not math.isfinite(probability) or not 0 <= probability <= 1):
            continue
        result[key] = {
            **prediction,
            "forecast_recorded_at": report["generated_at"],
            "source_retrieved_at": report["retrieved_at"],
            "scheduled_kickoff_at": game["start_date"],
            "model_id": model_id,
            "source": "generated_before_kickoff",
        }
    return result
