"""Dynamic team strength study: engine equivalence, tier semantics, no leakage, reproducible results."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dsb", ROOT / "scripts/dynamic_strength_backtest.py")
dsb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dsb)
from cfb_analytics.ratings import Game, Team, calculate_ratings  # noqa: E402


def fixture():
    teams = [Team("A", "X", 5.0), Team("B", "X", 0.0), Team("C", "Y", -3.0), Team("D", "Y", 1.0)]
    scores = [("A", "B", 31, 20), ("C", "D", 14, 21), ("A", "C", 28, 10), ("B", "D", 17, 24), ("D", "A", 20, 27),
              ("B", "C", 35, 3), ("A", "FCS U", 52, 7), ("C", "B", 21, 20)]
    return teams, [((0, i, ""), Game(h, a, hs, as_, i)) for i, (h, a, hs, as_) in enumerate(scores)]


def test_unit_weights_reproduce_the_incumbent_engine_exactly():
    teams, games = fixture()
    inc = calculate_ratings(teams, [g for _, g in games])
    mine = dsb.weighted_ratings(teams, games, dsb.incumbent)
    assert all(abs(inc[t].adaptive_rating - mine[t]) < 1e-12 for t in mine)


def test_latest_three_games_share_one_equal_weight_and_tiers_roll_forward():
    fn = dsb.tiered(1.25, 1.5, recent=3, mid=4)
    weights = [fn(rank, 10) for rank in range(10)]           # rank 0 = most recent
    assert weights[:3] == [1.5, 1.5, 1.5]                    # games 8-10: equal current-form weight
    assert weights[3:7] == [1.25] * 4 and weights[7:] == [1.0] * 3
    # One more game: the oldest "current form" game moves into the intermediate tier.
    assert [fn(r, 11) for r in range(11)][3] == 1.25
    assert all(fn(r, 3) == 1.5 for r in range(3))             # 3 or fewer games: all equal, identical to incumbent


def test_weights_are_normalized_per_team_so_prior_strength_is_unchanged():
    teams, games = fixture()
    fn = dsb.tiered(1.25, 2.0, 1, 1)
    a = dsb.weighted_ratings(teams, games, fn)
    b = dsb.weighted_ratings(teams, games, lambda rank, n: 3.0 * fn(rank, n))   # uniform rescale -> same ratings
    assert all(abs(a[t] - b[t]) < 1e-12 for t in a)


def test_form_term_uses_only_earlier_weeks():
    rows = [{"season": 2026, "week": (0, 1), "home": "A", "away": "B", "pred": 0.0, "actual": 30, "p": 0.5, "y": 1, "id": "1"},
            {"season": 2026, "week": (0, 2), "home": "A", "away": "B", "pred": 0.0, "actual": 0, "p": 0.5, "y": 0, "id": "2"}]
    out = dsb.form_adjusted(rows, 0.1)
    assert out[0]["pred"] == 0.0                                          # week 1: no history, no adjustment
    assert abs(out[1]["pred"] - 0.1 * (30 / 3 - (-30) / 3)) < 1e-12       # week 2 uses week 1 only


def test_committed_study_regenerates_identically():
    committed = json.loads((ROOT / "docs/evidence/dynamic-strength/study.json").read_text())
    fresh = json.loads(json.dumps(dsb.study(), sort_keys=True, default=list))
    assert fresh == committed
    held = committed["evaluation"]["heldout_2022_2025"]
    best = committed["preregistered_tiered"]
    lo, hi = held[best]["delta_brier"][1]
    assert lo <= 0 <= hi, "the tiered model's held-out Brier change is not distinguishable from zero"
