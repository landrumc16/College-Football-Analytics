import pytest

from cfb_analytics.v4_program_rankings import rank_programs


def rows(team, values, first=2016):
    return [{"team": team, "season": first + i, "strength": score,
             "source": f"verified-{first+i}"} for i, score in enumerate(values)]


def test_full_ten_five_three_year_rankings_and_trend_distinction():
    data = rows("Rising", list(range(10))) + rows("Falling", list(range(9, -1, -1)))
    report = rank_programs(data, 2025)
    teams = {p["team"]: p["windows"] for p in report["programs"]}
    assert report["status"] == "descriptive_only"
    assert not report["predictive_validation"]
    assert teams["Rising"]["10"]["rank"] == 1
    assert teams["Falling"]["10"]["rank"] == 1  # identical 10-year strength
    assert teams["Rising"]["3"]["rank"] == 1
    assert teams["Falling"]["3"]["rank"] == 2
    assert teams["Rising"]["5"]["strength"] == 7.0


def test_sparse_programs_have_no_imputed_rank():
    report = rank_programs(rows("Established", [4] * 10) + rows("New", [9] * 3, 2023), 2025)
    teams = {p["team"]: p["windows"] for p in report["programs"]}
    assert teams["New"]["10"]["rank"] is None
    assert teams["New"]["10"]["seasons_available"] == 3
    assert teams["New"]["3"]["rank"] == 1
    assert teams["Established"]["3"]["rank"] == 2


def test_no_future_data_duplicates_or_invalid_strength():
    with pytest.raises(ValueError, match="Duplicate"):
        rank_programs(rows("A", [1]) * 2, 2025)
    with pytest.raises(ValueError, match="completed"):
        rank_programs(rows("A", [1], 2026), 2025)
    with pytest.raises(ValueError, match="finite"):
        rank_programs(rows("A", [float("nan")]), 2025)
    with pytest.raises(ValueError, match="source"):
        rank_programs([dict(team="A", season=2025, strength=1, source="")], 2025)
    with pytest.raises(ValueError, match="Duplicate windows"):
        rank_programs([], 2025, (3, 3))
