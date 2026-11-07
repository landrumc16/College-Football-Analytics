import pytest

from cfb_analytics.v4_program_trajectory import program_trajectories


def season_rows(team, values, start=2016):
    return [dict(team=team, season=start + i, strength=float(value),
                 source=f"historical-{start+i}") for i, value in enumerate(values)]


def test_long_term_direction_and_recent_reversal():
    rows = season_rows("Rising", list(range(0, 40, 4)))
    rows += season_rows("Falling", list(range(40, 0, -4)))
    rows += season_rows("Flat", [12] * 10)
    rows += season_rows("Reversing", [2, 3, 4, 5, 6, 7, 8, 10, 7, 4])
    report = program_trajectories(rows, 2025)
    teams = {p["team"]: p for p in report["programs"]}
    assert teams["Rising"]["long_term"]["classification"] == "rapidly_rising"
    assert teams["Falling"]["long_term"]["classification"] == "rapidly_declining"
    assert teams["Flat"]["long_term"]["classification"] == "stable"
    assert teams["Reversing"]["recent"]["classification"] == "rapidly_declining"
    assert report["status"] == "descriptive_only"
    assert report["predictive_validation"] is False


def test_sparse_history_is_not_interpolated():
    report = program_trajectories(season_rows("New", [10, 12, 14], 2023), 2025)
    team = report["programs"][0]
    assert team["long_term"]["classification"] == "insufficient_data"
    assert team["recent"]["classification"] == "steadily_improving"
    assert team["long_term"]["slope_per_season"] is None


def test_reject_future_duplicates_invalid_values():
    with pytest.raises(ValueError, match="Duplicate"):
        program_trajectories(season_rows("A", [1]) * 2, 2025)
    with pytest.raises(ValueError, match="completed"):
        program_trajectories(season_rows("A", [1], 2026), 2025)
    with pytest.raises(ValueError, match="strength"):
        program_trajectories(season_rows("A", [float("inf")]), 2025)
    with pytest.raises(ValueError, match="threshold"):
        program_trajectories([], 2025, steady_threshold=3, rapid_threshold=2)
