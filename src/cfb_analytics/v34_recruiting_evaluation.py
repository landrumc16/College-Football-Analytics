"""End-to-end research evaluation of recruiting classes versus season records.

This pipeline intentionally does not claim historical pregame provenance.
"""
from .v34_recruiting_baseline import walkforward_recruiting_baseline
from .v34_recruiting_scorecard import recruiting_baseline_scorecard
from .v34_recruiting_leaderboard import recruiting_residual_leaderboard
from .v34_historical_records import historical_season_records


def evaluate_historical_recruiting(classes, raw_games_by_season, *, fbs_teams_by_season,
                                   completed_seasons, min_train_seasons=3):
    records = historical_season_records(raw_games_by_season,
                                        fbs_teams_by_season=fbs_teams_by_season,
                                        completed_seasons=completed_seasons)
    actual = {}
    for row in records:
        key = (row["season"], row["team"])
        if key in actual:
            raise ValueError("Duplicate actual team-season")
        actual[key] = row
    seen = set()
    joined = []
    skipped = {"incomplete_season": 0, "missing_actual": 0}
    for row in classes:
        key = (row["season"], row["team"])
        if key in seen:
            raise ValueError("Duplicate recruiting class")
        seen.add(key)
        if row["season"] not in completed_seasons:
            skipped["incomplete_season"] += 1
            continue
        record = actual.get(key)
        if record is None:
            skipped["missing_actual"] += 1
            continue
        if not row.get("source") or not row.get("retrieved_at"):
            raise ValueError("Missing recruiting provenance")
        joined.append({"season": row["season"], "team": row["team"],
                       "recruiting_points": row["recruiting_points"],
                       "actual_wins": record["actual_wins"],
                       "games_played": record["games_played"]})
    predictions = walkforward_recruiting_baseline(joined,
                                                   min_train_seasons=min_train_seasons)
    return {"scorecard": recruiting_baseline_scorecard(predictions),
            "program_recruiting_residuals": recruiting_residual_leaderboard(predictions),
            "holdout_predictions": predictions,
            "joined_team_seasons": len(joined), "excluded": skipped,
            "historical_asof_verified": False,
            "scope": "descriptive historical season-win benchmark; not verified pregame forecasts"}
