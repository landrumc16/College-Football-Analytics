"""V3.4 prospective grading: provider duplicates cannot inflate metrics."""
from cfb_analytics.pipeline import build_prediction_accuracy


def test_duplicate_completed_game_counts_once():
    game = {"game_id": 123, "completed": True, "home": "Georgia",
            "away": "Alabama", "home_score": 24, "away_score": 17,
            "start_date": "2026-10-01T18:00:00Z"}
    forecast = {"game_id": 123, "home": "Georgia", "away": "Alabama",
                "home_win_probability": 0.7, "home_margin": 4,
                "source": "generated_before_kickoff",
                "source_retrieved_at": "2026-09-30T12:00:00Z",
                "forecast_recorded_at": "2026-09-30T13:00:00Z",
                "scheduled_kickoff_at": "2026-10-01T18:00:00Z"}
    roster = {"Georgia", "Alabama"}
    single = build_prediction_accuracy({"games": [game]}, {"123": forecast}, roster)
    duplicated = build_prediction_accuracy({"games": [game, dict(game)]}, {"123": forecast}, roster)
    assert single == duplicated
    assert duplicated["games_evaluated"] == 1
    assert duplicated["eligible_completed_games"] == 1
