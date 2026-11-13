"""Reproduce the retained 2026 Week 10 FBS-only forecast scorecard from real inputs."""
import json
import math
from pathlib import Path

from cfb_analytics.v5_forecast_evaluation import evaluate_archived_forecasts

ROOT = Path(__file__).resolve().parents[1]


def test_committed_week10_fbs_scorecard_reproduces_from_frozen_ledger():
    ledger = json.loads((ROOT / "data/pregame-2026-history.json").read_text())
    report = json.loads((ROOT / "data/season-2026-report.json").read_text())
    archived = report["prediction_accuracy"]
    assert archived["evaluation_scope"] == "archived_pregame_fbs_vs_fbs"
    assert report["generated_at"] == "2026-11-09T21:28:51.040893+00:00"
    rows = []
    excluded_fcs = []
    for game in report["schedule"]:
        forecast = ledger.get(str(game["game_id"]))
        if not forecast or forecast.get("source") != "generated_before_kickoff":
            continue
        if not game["completed"] or game["home_score"] is None or game["away_score"] is None:
            continue
        if game["home_score"] == game["away_score"] or game["week"] != 10:
            continue
        assert (forecast["home"], forecast["away"]) == (game["home"], game["away"])
        if game["away"] == "Merrimack" or game["home"] == "Merrimack":
            excluded_fcs.append(game["game_id"])
            continue
        assert forecast["source_retrieved_at"] <= forecast["forecast_recorded_at"]
        rows.append({
            "game_id": str(game["game_id"]),
            "model_id": forecast["model_id"],
            "prediction_time": forecast["forecast_recorded_at"],
            "source_retrieved_at": forecast["source_retrieved_at"],
            "kickoff_time": forecast["scheduled_kickoff_at"],
            "home_win_probability": forecast["home_win_probability"],
            "home_won": game["home_score"] > game["away_score"],
        })
    assert excluded_fcs == [401858290]
    result = evaluate_archived_forecasts(rows)
    assert result["total_forecasts"] == archived["games_evaluated"] == 57
    stats = result["models"]["workbook_2026_baseline"]
    assert round(stats["accuracy"], 3) == archived["winner_accuracy"]
    assert round(stats["accuracy"] * stats["games"]) == archived["correct_winners"] == 35
    assert math.isclose(stats["brier"], archived["brier_score"], abs_tol=0.00005)
    assert math.isclose(stats["logloss"], archived["log_loss"], abs_tol=0.00005)
    assert sum(x["games"] for x in stats["calibration"]) == 57
