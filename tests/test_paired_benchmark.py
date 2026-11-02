"""Paired model comparisons must use the same eligible pregame fixtures."""
from cfb_analytics.historical import HistoricalGame
from cfb_analytics.historical_evaluation import ArchivedForecast
from cfb_analytics.paired_benchmark import paired_scorecard


def test_paired_comparison_excludes_unmatched_and_postgame():
    games = [
        HistoricalGame(season=2025, game_id=i, home="A", away="B",
                       home_division="FBS", away_division="FBS",
                       kickoff="2025-09-01T20:00:00Z",
                       source_retrieved_at="2025-09-01T16:00:00Z",
                       source="fixture", home_score=21, away_score=14)
        for i in (1, 2, 3)]
    workbook = [ArchivedForecast(2025, i, 0.6, "2025-09-01T18:00:00Z", "2025-09-01T17:00:00Z")
                for i in (1, 2, 3)]
    candidate = [
        ArchivedForecast(2025, 1, 0.8, "2025-09-01T19:00:00Z", "2025-09-01T17:00:00Z"),
        ArchivedForecast(2025, 2, 0.8, "2025-09-01T20:00:00Z", "2025-09-01T17:00:00Z")]
    result = paired_scorecard(games, workbook, candidate)
    assert result["paired_games"] == 1
    assert result["eligible_completed_games"] == 3
    assert result["excluded"]["missing_candidate"] == 1
    assert result["excluded"]["not_verified_pregame"] == 1
    assert round(result["workbook"]["brier_score"], 8) == 0.16
    assert round(result["candidate"]["brier_score"], 8) == 0.04
    assert result["by_season_counts"] == {"2025": 1}
    assert result["by_season"]["2025"]["workbook"]["games"] == 1
    assert result["by_season"]["2025"]["candidate"]["brier_score"] == result["candidate"]["brier_score"]


def test_no_intersection_does_not_claim_accuracy():
    assert paired_scorecard([], [], [])["workbook"] is None
