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


def test_pending_duplicate_does_not_hide_completed_result():
    completed = {"game_id": 456, "completed": True, "home": "Georgia",
                 "away": "Alabama", "home_score": 21, "away_score": 14,
                 "start_date": "2026-10-01T18:00:00Z"}
    pending = {**completed, "completed": False, "home_score": None, "away_score": None}
    forecast = {"home": "Georgia", "away": "Alabama",
                "home_win_probability": 0.65, "home_margin": 3,
                "source_retrieved_at": "2026-09-30T12:00:00Z",
                "forecast_recorded_at": "2026-09-30T13:00:00Z",
                "scheduled_kickoff_at": "2026-10-01T18:00:00Z"}
    for order in ([pending, completed], [completed, pending]):
        result = build_prediction_accuracy({"games": order}, {"456": forecast}, {"Georgia", "Alabama"})
        assert result["eligible_completed_games"] == 1
        assert result["games_evaluated"] == 1


def test_conflicting_final_scores_are_not_scored():
    first = {"game_id": 789, "completed": True, "home": "Georgia",
             "away": "Alabama", "home_score": 24, "away_score": 17,
             "start_date": "2026-10-01T18:00:00Z"}
    conflicting = {**first, "away_score": 28}
    result = build_prediction_accuracy({"games": [first, conflicting]}, {}, {"Georgia", "Alabama"})
    assert result["eligible_completed_games"] == 0
    assert result["games_evaluated"] == 0


def test_weekly_scorecard_uses_only_verified_unique_games():
    game = {"game_id": 901, "week": 9, "completed": True, "home": "Georgia",
            "away": "Alabama", "home_score": 31, "away_score": 21,
            "start_date": "2026-10-31T18:00:00Z"}
    forecast = {"home": "Georgia", "away": "Alabama",
                "home_win_probability": 0.8, "home_margin": 7,
                "source_retrieved_at": "2026-10-30T12:00:00Z",
                "forecast_recorded_at": "2026-10-30T13:00:00Z",
                "scheduled_kickoff_at": "2026-10-31T18:00:00Z"}
    result = build_prediction_accuracy({"games": [game, dict(game)]},
                                       {"901": forecast}, {"Georgia", "Alabama"})
    assert result["weekly_scorecard"] == [
        {"week": 9, "games_evaluated": 1, "correct_winners": 1,
         "winner_accuracy": 1.0, "brier_score": 0.04}]
    assert build_prediction_accuracy({"games": [game]}, {}, {"Georgia", "Alabama"})["weekly_scorecard"] == []


def test_team_performance_deduplicates_and_rejects_conflicts():
    from cfb_analytics.pipeline import build_performance_against_expectations
    game = {"game_id": 901, "completed": True, "home": "Georgia",
            "away": "Alabama", "home_score": 31, "away_score": 21,
            "start_date": "2026-10-31T18:00:00Z"}
    forecast = {"home": "Georgia", "away": "Alabama",
                "home_win_probability": 0.8,
                "source_retrieved_at": "2026-10-30T12:00:00Z",
                "forecast_recorded_at": "2026-10-30T13:00:00Z",
                "scheduled_kickoff_at": "2026-10-31T18:00:00Z"}
    roster = [{"name": "Georgia"}, {"name": "Alabama"}]
    once = build_performance_against_expectations({"games": [game]}, roster, {"901": forecast})
    twice = build_performance_against_expectations({"games": [game, dict(game)]}, roster, {"901": forecast})
    assert once == twice
    assert twice["Georgia"]["games_with_forecasts"] == 1
    conflict = {**game, "away_score": 35}
    rejected = build_performance_against_expectations({"games": [game, conflict]}, roster, {"901": forecast})
    assert rejected["Georgia"]["games_with_forecasts"] == 0
