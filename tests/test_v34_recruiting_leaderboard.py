import pytest
from cfb_analytics.v34_recruiting_leaderboard import recruiting_residual_leaderboard


def row(team, season, expected, actual):
    return {"team": team, "season": season, "expected_wins": expected,
            "actual_wins": actual, "games_played": 12,
            "train_through_season": season - 1, "historical_asof_verified": False}


def test_program_ranking_uses_only_heldout_residuals():
    rows = [row(t, y, e, a) for y in (2022, 2023, 2024)
            for t, e, a in (("A", 6, 9), ("B", 9, 6))]
    result = recruiting_residual_leaderboard(rows)
    assert [p["team"] for p in result["programs"]] == ["A", "B"]
    assert result["programs"][0]["average_wins_above_recruiting_baseline"] == 3
    assert result["programs"][1]["average_wins_above_recruiting_baseline"] == -3


def test_insufficient_seasons_and_duplicate_rejected():
    r = row("A", 2024, 6, 8)
    assert recruiting_residual_leaderboard([r])["programs"] == []
    with pytest.raises(ValueError, match="Duplicate"):
        recruiting_residual_leaderboard([r, r])
