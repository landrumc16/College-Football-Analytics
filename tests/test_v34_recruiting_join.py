import pytest
from cfb_analytics.v34_recruiting_join import evaluate_recruiting_residuals


def expectation(year, team="Georgia"):
    return {"season": year, "team": team, "recruiting_expectation_wins": 7,
            "source": "dated preseason forecast",
            "expectation_published_at": f"{year}-07-01T00:00:00Z",
            "season_start_at": f"{year}-08-01T00:00:00Z"}


def test_completed_seasons_only_and_no_missing_actual_imputation():
    actual = [{"season": y, "team": "Georgia", "actual_wins": 9,
               "games_played": 12} for y in (2022, 2023, 2024)]
    rows = [expectation(y) for y in (2022, 2023, 2024, 2025)]
    rows.append(expectation(2024, "Missing Team"))
    result = evaluate_recruiting_residuals(actual, rows,
                                          completed_seasons={2022, 2023, 2024})
    assert result["matched_team_seasons"] == 3
    assert result["excluded_incomplete_season"] == 1
    assert result["excluded_missing_actual"] == 1
    assert result["rankings"][0]["average_wins_above_recruiting_expectation"] == 2


def test_reject_duplicate_expectations():
    row = expectation(2024)
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_recruiting_residuals([], [row, row], completed_seasons={2024})
