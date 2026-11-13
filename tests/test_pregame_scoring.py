"""Scoring must never include hindsight or unverifiable archived forecasts."""
from cfb_analytics.pipeline import build_prediction_accuracy, build_performance_against_expectations


def game(start_date):
    return {"game_id": 7, "home": "Alabama", "away": "Auburn",
            "completed": True, "home_score": 28, "away_score": 21,
            "start_date": start_date}


def history(recorded_at):
    return {"7": {"home": "Alabama", "away": "Auburn",
                  "home_win_probability": 0.75,
                  "forecast_recorded_at": recorded_at}}


def test_accuracy_scores_only_proven_pregame_forecasts():
    for kickoff, published, expected in (
        ("2026-11-01T18:00:00Z", "2026-11-01T17:59:59Z", 1),
        ("2026-11-01T18:00:00Z", "2026-11-01T18:00:00Z", 0),
        ("2026-11-01T18:00:00Z", "2026-11-01T18:00:01Z", 0),
        (None, "2026-11-01T17:00:00Z", 0),
        ("2026-11-01T18:00:00Z", None, 0),
    ):
        result = build_prediction_accuracy({"games": [game(kickoff)]},
                                           history(published),
                                           eligible_teams={"Alabama", "Auburn"})
        assert result["games_evaluated"] == expected


def test_performance_excludes_unverifiable_history():
    roster = [{"name": "Alabama"}, {"name": "Auburn"}]
    for kickoff, expected in ((None, 0), ("2026-11-01T18:00:00Z", 1)):
        result = build_performance_against_expectations(
            {"games": [game(kickoff)]}, roster,
            history("2026-11-01T17:00:00Z"))
        assert result["Alabama"]["games_with_forecasts"] == expected
        assert result["Auburn"]["games_with_forecasts"] == expected


def test_neutral_baseline_uses_identical_verified_games():
    first = game("2026-11-01T18:00:00Z")
    second = {**first, "game_id": 8, "home_score": 14, "away_score": 21}
    forecasts = history("2026-11-01T17:00:00Z")
    forecasts["8"] = {**forecasts["7"], "home_win_probability": 0.2}
    result = build_prediction_accuracy({"games": [first, second]}, forecasts,
                                       eligible_teams={"Alabama", "Auburn"})
    assert result["games_evaluated"] == 2
    assert result["neutral_baseline"]["games"] == 2
    assert result["neutral_baseline"]["winner_accuracy"] == 0.5
    assert result["neutral_baseline"]["brier_score"] == 0.25
    assert result["neutral_baseline"]["log_loss"] == 0.6931


def test_neutral_baseline_does_not_claim_accuracy_without_archive():
    result = build_prediction_accuracy({"games": [game("2026-11-01T18:00:00Z")]}, {},
                                       eligible_teams={"Alabama", "Auburn"})
    assert result["neutral_baseline"]["games"] == 0
    assert result["neutral_baseline"]["winner_accuracy"] is None
    assert result["neutral_baseline"]["brier_score"] is None
    assert result["neutral_baseline"]["log_loss"] is None
