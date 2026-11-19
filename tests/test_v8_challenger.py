"""V8 challenger mechanics: solver, calibration, bootstrap, schedule ordering, replay and leakage."""
import copy
import itertools
import math
import random

from cfb_analytics import v8_challenger as ch
from cfb_analytics.backtest import backtest_weeks
from cfb_analytics.ratings import Game, Team

from test_v8_stats import counts, game


def test_solver_and_ridge_recover_linear_truth():
    assert [round(v, 6) for v in ch.solve([[2, 1], [1, 3]], [3, 5])] == [0.8, 1.4]
    rng = random.Random(1)
    xs = [{"gap": rng.uniform(-20, 20), "efficiency:epa": rng.uniform(-1, 1)} for _ in range(400)]
    ys = [0.9 * x["gap"] + 6 * x["efficiency:epa"] + 2 for x in xs]
    model = ch.Ridge(["gap", "efficiency:epa"], l2=1e-6).fit(xs, ys)
    coef = model.coefficients()
    assert abs(coef["gap"] - 0.9) < 1e-3 and abs(coef["efficiency:epa"] - 6) < 1e-2


def test_fit_scale_and_calibration_slope():
    rng = random.Random(2)
    margins = [rng.uniform(-30, 30) for _ in range(4000)]
    outcomes = [int(rng.random() < 1 / (1 + math.exp(-m / 12))) for m in margins]
    assert abs(ch.fit_scale(margins, outcomes) - 12) < 1.5
    probs = [1 / (1 + math.exp(-m / 12)) for m in margins]
    assert abs(ch.calibration_slope(probs, outcomes) - 1) < 0.1
    overconfident = [1 / (1 + math.exp(-m / 6)) for m in margins]
    assert ch.calibration_slope(overconfident, outcomes) < 0.7


def test_clustered_bootstrap_detects_a_clear_improvement():
    rng = random.Random(3)
    recs = []
    for i in range(600):
        y = int(rng.random() < 0.7)
        recs.append({"season": 2020 + i % 5, "week": i % 12, "y": y, "c": 0.7, "b": 0.5})
    lo, hi = ch.clustered_bootstrap(recs, "c", "b", draws=500)
    assert hi < 0  # challenger Brier lower in every resample


def rows_fixture():
    confs = dict.fromkeys("ABCDEF", "SEC")
    rows = []
    for i, (h, a) in enumerate(itertools.combinations("ABCDEF", 2)):
        week = i // 3 + 1
        rows += game(i + 1, f"2025-09-{week:02d}", h, a, counts(60, 30 + i % 7, pts=21 + 2 * (i % 5)), counts(60, 25 + i % 5, pts=14 + 2 * (i % 4)), confs)
        for r in rows[-2:]:
            r["week"] = week
    post = game(99, "2025-12-20", "A", "B", counts(60, 33, pts=31), counts(60, 28, pts=24), confs)
    for r in post:
        r["season_type"], r["week"] = "postseason", 1
    return rows + post


def test_season_games_orders_weeks_and_places_postseason_last():
    games = ch.season_games(rows_fixture())
    assert len(games) == 16 and games[-1]["game_id"] == "99"
    assert games[-1]["week"] == max(g["week"] for g in games[:-1]) + 1
    assert all(g["home"] != g["away"] for g in games)


def test_replay_matches_the_incumbent_backtest_engine():
    rows = rows_fixture()
    gaps, final = ch.replay_incumbent(rows, 2025, {})
    games = ch.season_games(rows)
    teams = [Team(t, "SEC", ch.SETTINGS.new_team_rating) for t in "ABCDEF"]
    hist = [Game(g["home"], g["away"], g["home_score"], g["away_score"], g["week"]) for g in games]
    report = backtest_weeks(teams, hist, ch.SETTINGS)
    assert report["games"] == len(gaps) == 16
    assert set(final) == set("ABCDEF")


def test_features_use_only_earlier_weeks():
    rows = rows_fixture()
    target = next(g for g in ch.season_games(rows) if g["week"] == 5)
    cutoff = target["date"][:10]
    snap = ch.snapshot(rows, cutoff)
    future = copy.deepcopy(rows)
    for r in future:
        if r["date"] >= cutoff:
            r["off"]["succ"] = r["off"]["plays"]
            r["off"]["ppa"] = 99.0
    assert ch.features(target, ch.snapshot(future, cutoff), 1.0) == ch.features(target, snap, 1.0)


def test_features_require_enough_prior_games():
    rows = rows_fixture()
    first = ch.season_games(rows)[0]
    assert ch.features(first, ch.snapshot(rows, first["date"][:10]), 0.0) is None
