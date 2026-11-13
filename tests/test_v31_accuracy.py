"""Prospective accuracy metrics and FBS population checks."""
import math
from cfb_analytics.pipeline import build_prediction_accuracy


def game(i, home, away, hs, ass):
    return {"game_id": i, "home": home, "away": away, "completed": True,
            "home_score": hs, "away_score": ass, "start_date": "2026-11-07T18:00:00Z"}


def forecast(home, away, probability, margin):
    return {"home": home, "away": away, "home_win_probability": probability,
            "home_margin": margin, "forecast_recorded_at": "2026-11-06T18:00:00Z",
            "source_retrieved_at": "2026-11-06T17:59:00Z",
            "scheduled_kickoff_at": "2026-11-07T18:00:00Z",
            "source": "generated_before_kickoff", "model_id": "workbook_2026_baseline"}


def test_margin_logloss_and_calibration_are_archived_only():
    snapshot = {"games": [game(1, "A", "B", 24, 14), game(2, "B", "A", 7, 17)]}
    history = {"1": forecast("A", "B", .8, 7), "2": forecast("B", "A", .2, -6)}
    result = build_prediction_accuracy(snapshot, history, eligible_teams={"A", "B"})
    assert result["games_evaluated"] == 2
    assert result["eligible_completed_games"] == 2
    assert result["forecast_coverage"] == 1.0
    assert result["winner_accuracy"] == 1.0
    assert result["brier_score"] == .04
    assert result["log_loss"] == round(-math.log(.8), 4)
    assert result["margin_mae"] == 3.5
    assert result["margin_games"] == 2
    assert sum(bucket["games"] for bucket in result["calibration"]) == 2


def test_empty_forecasts_do_not_invent_calibration_or_errors():
    result = build_prediction_accuracy({"games": [game(1, "A", "B", 24, 14)]}, {})
    assert result["games_evaluated"] == 0
    assert result["eligible_completed_games"] == 1
    assert result["forecast_coverage"] == 0.0
    assert result["log_loss"] is None
    assert result["margin_mae"] is None
    assert all(bucket["games"] == 0 and bucket["mean_predicted"] is None
               for bucket in result["calibration"])


def test_fcs_excluded_from_fbs_accuracy_but_can_be_scored_separately():
    snapshot = {"games": [game(1, "A", "FCS Opponent", 21, 7)]}
    history = {"1": forecast("A", "FCS Opponent", .7, 8)}
    assert build_prediction_accuracy(snapshot, history, {"A"})["games_evaluated"] == 0
    assert build_prediction_accuracy(snapshot, history)["games_evaluated"] == 1


def test_legacy_forecast_cannot_enter_published_accuracy():
    snapshot = {"games": [game(1, "A", "B", 24, 14)]}
    legacy = forecast("A", "B", .8, 7)
    legacy.pop("source_retrieved_at")
    legacy["source"] = "previously_published_forecast"
    result = build_prediction_accuracy(snapshot, {"1": legacy}, eligible_teams={"A", "B"})
    assert result["games_evaluated"] == 0
    assert result["winner_accuracy"] is None


def test_mismatched_kickoff_excluded_from_accuracy():
    snapshot = {"games": [game(1, "A", "B", 24, 14)]}
    row = forecast("A", "B", .8, 7)
    row["scheduled_kickoff_at"] = "2026-11-08T18:00:00Z"
    assert build_prediction_accuracy(snapshot, {"1": row})["games_evaluated"] == 0
