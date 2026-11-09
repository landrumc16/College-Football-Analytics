"""M4 pregame forecast evaluation: reject leakage and invalid archives."""
import math

import pytest

from cfb_analytics.v5_forecast_evaluation import evaluate_archived_forecasts


def forecast(game="g1", probability=0.8, won=True):
    return {
        "game_id": game,
        "model_id": "incumbent",
        "prediction_time": "2025-09-01T15:00:00Z",
        "kickoff_time": "2025-09-02T18:00:00-05:00",
        "home_win_probability": probability,
        "home_won": won,
    }


def test_metrics_are_reproducible_and_calibration_is_counted():
    result = evaluate_archived_forecasts([forecast(), forecast("g2", 0.2, False)])
    stats = result["models"]["incumbent"]
    assert stats["games"] == 2
    assert stats["brier"] == pytest.approx(0.04)
    assert stats["accuracy"] == 1
    assert stats["logloss"] == pytest.approx(-math.log(0.8))
    assert sum(bin_["games"] for bin_ in stats["calibration"]) == 2
    assert result["predictive_promotion_authorized"] is False


def test_no_records_cannot_claim_accuracy():
    assert evaluate_archived_forecasts([])["models"] == {}


@pytest.mark.parametrize("changes", [
    {"prediction_time": "2025-09-03T00:00:00Z"},
    {"prediction_time": "2025-09-02T23:00:00Z", "kickoff_time": "2025-09-02T23:00:00Z"},
    {"prediction_time": "2025-09-01T15:00:00"},
    {"home_win_probability": -0.1},
    {"home_win_probability": 1.1},
    {"home_win_probability": float("nan")},
    {"home_win_probability": True},
    {"home_won": 1},
    {"home_won": None},
    {"game_id": ""},
    {"model_id": ""},
])
def test_invalid_or_leaky_archive_is_rejected(changes):
    row = forecast()
    row.update(changes)
    with pytest.raises(ValueError):
        evaluate_archived_forecasts([row])


def test_duplicate_game_model_is_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_archived_forecasts([forecast(), forecast()])


def test_same_game_different_models_are_independently_reported():
    other = forecast()
    other["model_id"] = "baseline"
    result = evaluate_archived_forecasts([forecast(), other])
    assert set(result["models"]) == {"baseline", "incumbent"}


def test_paired_comparison_uses_only_common_games():
    a1 = forecast("g1", 0.8, True)
    a2 = forecast("g2", 0.1, False)
    b1 = forecast("g1", 0.6, True)
    b1["model_id"] = "baseline"
    result = evaluate_archived_forecasts([a1, a2, b1])
    comparison = result["paired_baseline_comparisons"][0]
    assert comparison["matched_games"] == 1
    assert comparison["model_a"] == "baseline"
    assert comparison["model_a_brier"] == pytest.approx(0.16)
    assert comparison["model_b_brier"] == pytest.approx(0.04)


def test_conflicting_outcomes_for_same_game_are_rejected():
    other = forecast("g1", 0.2, False)
    other["model_id"] = "baseline"
    with pytest.raises(ValueError, match="Conflicting final outcomes"):
        evaluate_archived_forecasts([forecast(), other])
