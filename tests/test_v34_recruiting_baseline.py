import pytest
from cfb_analytics.v34_recruiting_baseline import walkforward_recruiting_baseline


def test_walkforward_never_trains_on_holdout_season():
    rows = [{"season": y, "team": t, "recruiting_points": p,
             "actual_wins": w, "games_played": 12}
            for y in range(2019, 2024)
            for t, p, w in (("A", 300, 10), ("B", 100, 3))]
    output = walkforward_recruiting_baseline(rows)
    assert {r["season"] for r in output} == {2022, 2023}
    assert all(r["train_through_season"] < r["season"] for r in output)
    assert all(r["historical_asof_verified"] is False for r in output)
    a = next(r for r in output if r["season"] == 2023 and r["team"] == "A")
    assert a["expected_wins"] > 6


def test_duplicate_team_season_rejected():
    row = {"season": 2022, "team": "A", "recruiting_points": 200,
           "actual_wins": 8, "games_played": 12}
    with pytest.raises(ValueError, match="Duplicate"):
        walkforward_recruiting_baseline([row, row])
