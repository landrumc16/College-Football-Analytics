import pytest

from cfb_analytics.ratings import Game, Team
from cfb_analytics.v32_experiments import CANDIDATES, compare_candidates


TEAMS = [Team("A", "ACC", 10), Team("B", "ACC", -10)]


def test_candidates_use_same_games_and_never_authorize_promotion():
    games = [Game("A", "B", 28, 14, 1), Game("A", "FCS", 35, 7, 2)]
    report = compare_candidates(TEAMS, games)
    assert report["games"] == 2
    assert report["holdout_validated"] is False
    assert report["promotion_authorized"] is False
    assert set(report["candidates"]) == set(CANDIDATES)
    for candidate in report["candidates"].values():
        assert candidate["games"] == report["games"]
        assert candidate["delta_vs_incumbent"]["brier_reduction"] == pytest.approx(
            report["incumbent"]["brier_score"] - candidate["model"]["brier_score"])
        assert candidate["matchup_diagnostics"]["fbs_fcs"]["games"] == 1


def test_candidates_handle_no_completed_games():
    report = compare_candidates(TEAMS, [])
    assert report["games"] == 0
    assert report["incumbent"] is None
    assert all(row["delta_vs_incumbent"] is None for row in report["candidates"].values())


def test_candidates_reject_invalid_historical_ties():
    with pytest.raises(ValueError, match="cannot be tied"):
        compare_candidates(TEAMS, [Game("A", "B", 7, 7, 1)])
