import pytest

from cfb_analytics.v4_schedule_context import season_schedule_context


def game(game_id, home, away, hs, aws, away_division="FBS"):
    return {"season": 2025, "game_id": game_id, "week": 1,
            "kickoff": "2025-09-01T17:00:00+00:00",
            "home": home, "away": away, "home_score": hs, "away_score": aws,
            "home_division": "FBS", "away_division": away_division,
            "fbs_game": away_division == "FBS", "fbs_participant": True}


def ratings():
    return {"season": 2025, "status": "retrospective_schedule_adjusted_research_only",
            "teams": [{"team": "A", "rating": 1520.0},
                      {"team": "B", "rating": 1550.0},
                      {"team": "C", "rating": 1450.0}]}


def test_opponent_quality_and_non_fbs_are_separate():
    games = [game("1", "A", "B", 21, 14),
             game("2", "A", "C", 28, 7),
             game("3", "A", "D", 35, 3, "FCS")]
    result = season_schedule_context(games, ratings(), 2025)
    teams = {r["team"]: r for r in result["teams"]}
    assert teams["A"]["fbs_opponent_count"] == 2
    assert teams["A"]["other_opponent_count"] == 1
    assert teams["A"]["mean_fbs_opponent_elo"] == 1500
    assert teams["A"]["wins_vs_above_1500_fbs"] == 1
    assert teams["B"]["losses_vs_above_1500_fbs"] == 1
    assert result["pregame_available"] is False


def test_missing_opponent_rating_rejected():
    with pytest.raises(ValueError, match="Missing FBS opponent rating"):
        season_schedule_context([game("1", "A", "Missing", 21, 14)], ratings(), 2025)


def test_wrong_season_rejected():
    with pytest.raises(ValueError, match="match"):
        season_schedule_context([game("1", "A", "B", 21, 14)], {**ratings(), "season": 2024}, 2025)
