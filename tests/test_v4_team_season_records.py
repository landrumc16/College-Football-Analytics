import pytest

from cfb_analytics.v4_team_season_records import team_season_records


def game(game_id, home, away, hs, aws, away_division="FBS"):
    return {
        "season": 2025, "game_id": game_id, "week": 1,
        "kickoff": "2025-09-01T17:00:00+00:00",
        "home": home, "away": away,
        "home_score": hs, "away_score": aws,
        "home_division": "FBS", "away_division": away_division,
        "fbs_game": away_division == "FBS", "fbs_participant": True,
    }


def test_counts_both_sides_and_separates_fcs_opponents():
    games = [game("1", "A", "B", 21, 14), game("2", "A", "C", 31, 7, "FCS")]
    report = team_season_records(games, 2025)
    assert report["team_count"] == 2
    a, b = report["teams"]
    assert a["team"] == "A"
    assert (a["wins"], a["fbs_wins"], a["other_wins"]) == (2, 1, 1)
    assert (a["points_for"], a["points_against"]) == (52, 21)
    assert (b["losses"], b["fbs_losses"]) == (1, 1)
    assert report["opponent_adjusted"] is False
    assert report["pregame_available"] is False


def test_duplicate_game_rejected():
    row = game("1", "A", "B", 21, 14)
    with pytest.raises(ValueError, match="duplicate"):
        team_season_records([row, row], 2025)


def test_source_identity_not_silently_merged():
    report = team_season_records([
        game("1", "A", "B", 21, 14),
        game("2", "A State", "B", 21, 14),
    ], 2025)
    assert report["team_count"] == 3
