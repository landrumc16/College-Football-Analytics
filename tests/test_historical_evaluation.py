"""Verify V2 scoring uses only eligible archived pregame FBS forecasts."""
import pytest

from cfb_analytics.historical import HistoricalGame
from cfb_analytics.historical_evaluation import ArchivedForecast, evaluate_forecasts


def game(game_id=1, season=2025, away_division="FBS"):
    return HistoricalGame(
        season=season, game_id=game_id, home="A", away="B",
        home_division="FBS", away_division=away_division,
        kickoff="2025-09-01T20:00:00Z",
        source_retrieved_at="2025-09-01T17:00:00Z",
        source="CFBD", home_score=21, away_score=14)


def forecast(game_id=1, season=2025, probability=0.8,
             generated_at="2025-09-01T18:00:00Z"):
    return ArchivedForecast(season, game_id, probability, generated_at)


def test_valid_forecast_scores():
    result = evaluate_forecasts([game()], [forecast()])
    assert result["games"] == 1
    assert result["metrics"]["winner_accuracy"] == 1
    assert result["metrics"]["brier_score"] == pytest.approx(0.04)
    assert result["by_season"]["2025"]["games"] == 1


def test_ineligible_forecasts_not_counted():
    result = evaluate_forecasts(
        [game(), game(2, away_division="FCS")],
        [forecast(), forecast(2), forecast(1, generated_at="2025-09-01T20:00:00Z")]
    ) if False else evaluate_forecasts(
        [game(), game(2, away_division="FCS"), game(3)],
        [forecast(), forecast(2), forecast(3, generated_at="2025-09-01T20:00:00Z"),
         forecast(999)])
    assert result["games"] == 1
    assert result["excluded"] == {
        "unknown_game": 1, "ineligible_game": 1, "not_pregame": 1}


def test_empty_sample_has_no_accuracy():
    result = evaluate_forecasts([game(away_division="FCS")], [forecast()])
    assert result["metrics"] is None
    assert result["games"] == 0


def test_reordered_input_deterministic_and_multiseason():
    records = [game(2, season=2024), game(1)]
    predictions = [forecast(1), forecast(2, season=2024, probability=0.4)]
    assert evaluate_forecasts(records, predictions) == evaluate_forecasts(
        list(reversed(records)), list(reversed(predictions)))


def test_duplicate_forecasts_rejected():
    with pytest.raises(ValueError, match="Duplicate forecasts"):
        evaluate_forecasts([game()], [forecast(), forecast()])


def test_invalid_probabilities_rejected():
    with pytest.raises(ValueError):
        forecast(probability=1.1)
