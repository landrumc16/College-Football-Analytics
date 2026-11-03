import pytest
from cfb_analytics.v34_recruiting_results import recruiting_vs_results


def class_row(y):
    return {"season": y, "team": "Georgia", "recruiting_points": 300.0,
            "source": "CFBD recruiting/teams", "retrieved_at": "2026-11-03T00:00:00Z"}


def test_recruiting_results_descriptive_join():
    years = (2022, 2023, 2024)
    actual = [{"season": y, "team": "Georgia", "actual_wins": 10,
               "games_played": 12} for y in years]
    result = recruiting_vs_results([class_row(y) for y in years] + [class_row(2025)],
                                   actual, completed_seasons=set(years))
    assert result["teams"][0]["win_rate"] == 10/12
    assert result["matched_team_seasons"] == 3
    assert result["excluded"]["incomplete_season"] == 1


def test_duplicate_class_rejected():
    row = class_row(2024)
    with pytest.raises(ValueError, match="Duplicate"):
        recruiting_vs_results([row, row], [], completed_seasons={2024})
