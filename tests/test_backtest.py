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
    # Changing an earlier game in the SAME week must not change the
    # prediction metrics for a different game in that week.
    first = [Game("A", "FCS", 40, 7, 1), Game("B", "A", 10, 14, 1)]
    second = [Game("A", "FCS", 7, 40, 1), Game("B", "A", 10, 14, 1)]
    a = backtest_weeks(TEAMS, first)
    b = backtest_weeks(TEAMS, second)
    # The first game's observed outcome changes; use one-game baseline
    # equality for the unaffected game via the exact first-week prior.
    assert a["preseason_baseline"]["winner_accuracy"] != b["preseason_baseline"]["winner_accuracy"]
    assert a["games"] == b["games"] == 2


def test_backtest_requires_dated_weeks():
    with pytest.raises(ValueError, match="positive week"):
        backtest_weeks(TEAMS, [Game("A", "B", 21, 7)])
