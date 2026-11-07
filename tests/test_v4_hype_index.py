import pytest

from cfb_analytics.v4_hype_index import historical_hype


def row(year, preseason, final, poll="AP", team="A"):
    return dict(team=team, season=year, poll=poll, preseason_rank=preseason,
                final_rank=final, source=f"poll-archive-{year}")


def test_ranked_dropouts_and_unranked_entries_are_distinct():
    result = historical_hype([
        row(2022, 4, None), row(2023, None, 18),
        row(2024, 7, 16), row(2025, 8, 20),
        row(2025, 6, 3, poll="Coaches"),
    ], 2025)
    ap = next(p for p in result["program_polls"] if p["poll"] == "AP")
    coaches = next(p for p in result["program_polls"] if p["poll"] == "Coaches")
    assert ap["preseason_top25"] == 3
    assert ap["dropped_out"] == 1
    assert ap["entered_top25"] == 1
    assert ap["retention_rate"] == pytest.approx(2 / 3)
    assert ap["within_poll_mean_rank_drop"] > 0
    assert ap["historical_tendency"] == "insufficient_data"
    assert coaches["preseason_top25"] == 1
    assert not result["predictive_validation"]


def test_three_ranked_comparisons_classify_historical_tendency():
    result = historical_hype([row(2023, 5, 15), row(2024, 6, 16),
                              row(2025, 7, 17)], 2025)
    assert result["program_polls"][0]["historical_tendency"] == "insufficient_data"
    assert result["program_polls"][0]["full_window_coverage"] is False


def test_complete_window_classifies_historical_tendency():
    result = historical_hype([row(year, 5, 15) for year in range(2016, 2026)], 2025)
    record = result["program_polls"][0]
    assert record["full_window_coverage"] is True
    assert record["seasons_required"] == 10
    assert record["historical_tendency"] == "historically_overhyped"


def test_missing_and_invalid_rank_rejected_without_inventing_26():
    with pytest.raises(ValueError, match="Rank"):
        historical_hype([row(2025, 26, None)], 2025)
    with pytest.raises(ValueError, match="Duplicate"):
        historical_hype([row(2025, 1, 2)] * 2, 2025)
    with pytest.raises(ValueError, match="completed"):
        historical_hype([row(2026, 1, 2)], 2025)
    with pytest.raises(ValueError, match="Poll"):
        historical_hype([row(2025, 1, 2, poll="CFP")], 2025)
