import pytest

from cfb_analytics.backtest import backtest_weeks
from cfb_analytics.ratings import Game, Team


TEAMS = [Team("A", "ACC", 10), Team("B", "ACC", -10)]


def test_weekly_backtest_scores_fbs_and_fcs_with_baseline():
    games = [Game("A", "B", 28, 14, 1),
             Game("A", "FCS", 35, 7, 2),
             Game("B", "A", 7, 21, 3)]
    result = backtest_weeks(TEAMS, games)
    assert result["games"] == 3
    for name in ("model", "preseason_baseline"):
        assert 0 <= result[name]["winner_accuracy"] <= 1
        assert 0 <= result[name]["brier_score"] <= 1
        assert result[name]["log_loss"] >= 0


def test_weekly_backtest_does_not_leak_same_week_scores():
    # A game against an FCS opponent has a different result in the same week.
    # The B-versus-A forecast must remain unchanged.
    from cfb_analytics.model import win_probability_from_rating_gap
    first = [Game("A", "FCS", 40, 7, 1), Game("B", "A", 10, 14, 1)]
    second = [Game("A", "FCS", 7, 40, 1), Game("B", "A", 10, 14, 1)]
    a = backtest_weeks(TEAMS, first)
    b = backtest_weeks(TEAMS, second)
    assert a["games"] == b["games"] == 2
    # Both games in week 1 use preseason priors; thus the evolving model
    # and fixed-preseason baseline must be identical despite changed results.
    assert a["model"] == a["preseason_baseline"]
    assert b["model"] == b["preseason_baseline"]
    assert a["model"]["winner_accuracy"] != b["model"]["winner_accuracy"]



def test_backtest_requires_dated_weeks():
    with pytest.raises(ValueError, match="positive week"):
        backtest_weeks(TEAMS, [Game("A", "B", 21, 7)])
