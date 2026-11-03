import pytest
from cfb_analytics.v34_overperformance import talent_overperformance


def season(year, team, actual, expected):
    return {"season": year, "team": team, "actual_wins": actual,
            "recruiting_expectation_wins": expected, "games_played": 12,
            "source": "dated independent preseason estimate",
            "expectation_published_at": f"{year}-07-01T00:00:00Z",
            "season_start_at": f"{year}-08-01T00:00:00Z"}


def test_rank_multi_season_residuals_without_fabricated_coverage():
    rows = [season(y, "Team A", 9, 6) for y in (2022, 2023, 2024)]
    rows += [season(y, "Team B", 4, 6) for y in (2022, 2023, 2024)]
    rows += [season(2024, "Team C", 12, 1)]
    result = talent_overperformance(rows)
    assert [r["team"] for r in result] == ["Team A", "Team B"]
    assert result[0]["average_wins_above_recruiting_expectation"] == 3


def test_reject_leakage_duplicates_and_missing_expectations():
    row = season(2024, "Team A", 8, 6)
    for invalid in ({**row, "expectation_published_at": "2024-09-01T00:00:00Z"},
                    {**row, "recruiting_expectation_wins": None},
                    {**row, "actual_wins": 13}):
        with pytest.raises(ValueError):
            talent_overperformance([invalid], min_seasons=1)
    with pytest.raises(ValueError):
        talent_overperformance([row, row], min_seasons=1)
