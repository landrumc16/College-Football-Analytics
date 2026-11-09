import pytest

from cfb_analytics.v4_scale_diagnostics import compare_season_scales


def report(season, ratings):
    return {"season": season, "status": "retrospective_schedule_adjusted_research_only",
            "teams": [{"team": f"T{i}", "rating": rating} for i, rating in enumerate(ratings)]}


def test_distribution_diagnostic_is_explicitly_not_publishable():
    result = compare_season_scales([report(2025, [1400, 1500, 1600]),
                                    report(2024, [1300, 1500, 1700])], minimum_teams=3)
    assert [s["season"] for s in result["seasons"]] == [2024, 2025]
    assert result["seasons"][1]["mean_rating"] == 1500
    assert result["seasons"][1]["population_sd"] > 0
    assert result["program_rankings_publishable"] is False


def test_duplicate_seasons_and_teams_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        compare_season_scales([report(2025, [1400, 1600]), report(2025, [1400, 1600])], minimum_teams=2)
    duplicate = report(2025, [1400, 1600])
    duplicate["teams"][1]["team"] = "T0"
    with pytest.raises(ValueError, match="duplicate team"):
        compare_season_scales([duplicate], minimum_teams=2)


def test_sparse_or_degenerate_seasons_rejected():
    with pytest.raises(ValueError, match="Insufficient"):
        compare_season_scales([report(2025, [1400, 1600])], minimum_teams=3)
    with pytest.raises(ValueError, match="Degenerate"):
        compare_season_scales([report(2025, [1500, 1500])], minimum_teams=2)
