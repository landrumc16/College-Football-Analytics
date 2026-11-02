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


def test_fcs_baseline_uses_fixed_opponent_rating_when_priors_weighted():
    from cfb_analytics.model import ModelSettings

    settings = ModelSettings(prior_year_weight=0.5)
    # In week one, both forecasts must match, even for an FCS opponent.
    result = backtest_weeks(TEAMS, [Game("A", "FCS", 21, 7, 1)], settings)
    assert result["games"] == 1
    assert result["model"] == result["preseason_baseline"]


def test_improvement_metrics_and_weekly_coverage_are_consistent():
    games = [Game("A", "B", 28, 14, 1),
             Game("A", "FCS", 35, 7, 2),
             Game("B", "A", 7, 21, 3)]
    report = backtest_weeks(TEAMS, games)
    assert report["weekly_coverage"] == [
        {"week": 1, "games": 1},
        {"week": 2, "games": 1},
        {"week": 3, "games": 1},
    ]
    assert sum(row["games"] for row in report["weekly_coverage"]) == report["games"]
    delta = report["improvement_vs_preseason"]
    assert delta["winner_accuracy_percentage_points"] == pytest.approx(
        100 * (report["model"]["winner_accuracy"] -
               report["preseason_baseline"]["winner_accuracy"]))
    assert delta["brier_score_reduction"] == pytest.approx(
        report["preseason_baseline"]["brier_score"] - report["model"]["brier_score"])
    assert delta["log_loss_reduction"] == pytest.approx(
        report["preseason_baseline"]["log_loss"] - report["model"]["log_loss"])



def test_v32_weekly_diagnostics_match_aggregate_brier_and_coverage():
    games = [Game("A", "B", 28, 14, 1),
             Game("A", "FCS", 35, 7, 2),
             Game("B", "A", 7, 21, 3)]
    report = backtest_weeks(TEAMS, games)
    weeks = report["weekly_diagnostics"]
    assert [w["week"] for w in weeks] == [1, 2, 3]
    assert sum(w["games"] for w in weeks) == report["games"]
    for key, aggregate in (("model_brier", "model"), ("baseline_brier", "preseason_baseline")):
        weighted = sum(w[key] * w["games"] for w in weeks) / report["games"]
        assert weighted == pytest.approx(report[aggregate]["brier_score"])
    assert weeks[0]["model_brier"] == pytest.approx(weeks[0]["baseline_brier"])


def test_v32_weekly_diagnostics_skip_unranked_fcs_only_games():
    report = backtest_weeks(TEAMS, [
        Game("FCS-1", "FCS-2", 21, 14, 1),
        Game("A", "FCS-1", 35, 7, 2),
    ])
    assert report["games"] == 1
    assert report["weekly_diagnostics"][0]["week"] == 2


def test_v32_weekly_diagnostics_empty_and_invalid_inputs():
    empty = backtest_weeks(TEAMS, [])
    assert empty["games"] == 0
    assert empty["model"] is None
    with pytest.raises(ValueError, match="cannot be tied"):
        backtest_weeks(TEAMS, [Game("A", "B", 7, 7, 1)])
    with pytest.raises(ValueError, match="positive week"):
        backtest_weeks(TEAMS, [Game("A", "B", 7, 3, 0)])
