import pytest
from cfb_analytics.v34_recruiting_scorecard import recruiting_baseline_scorecard


def record(season, expected, actual):
    return {"season": season, "team": "Georgia", "expected_wins": expected,
            "actual_wins": actual, "games_played": 12,
            "train_through_season": season - 1,
            "historical_asof_verified": False}


def test_holdout_error_metrics_and_season_coverage():
    result = recruiting_baseline_scorecard([record(2022, 8, 10), record(2023, 9, 8)])
    assert result["evaluated_team_seasons"] == 2
    assert result["sufficient_seasons"]
    assert result["win_mae"] == 1.5
    assert result["win_rmse"] == pytest.approx((2.5)**0.5)
    assert result["promotion_status"].startswith("research_only")


def test_reject_future_training_and_duplicates():
    row = record(2023, 9, 8)
    with pytest.raises(ValueError, match="Duplicate"):
        recruiting_baseline_scorecard([row, row])
    with pytest.raises(ValueError, match="Training"):
        recruiting_baseline_scorecard([{**row, "train_through_season": 2023}])
