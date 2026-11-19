"""Dual projection engine: weights, shared opponent fit, clipping, recency response and record distributions."""
import itertools
import math

from cfb_analytics import dual_projection as dp


def row(gid, date, team, opp, pf, pa, site, fbs=True, opp_fbs=True):
    return {"game_id": str(gid), "date": date, "team": team, "opp": opp, "pf": pf, "pa": pa, "site": site,
            "team_fbs": fbs, "opp_fbs": opp_fbs}


def game(gid, date, home, away, hp, ap, neutral=False):
    return [row(gid, date, home, away, hp, ap, "neutral" if neutral else "home"),
            row(gid, date, away, home, ap, hp, "neutral" if neutral else "away")]


def test_weights_are_stair_steps_with_mean_one():
    for kind in (None, "linear", 0.8):
        w = dp.weights(5, kind)
        assert abs(sum(w) - 5) < 1e-12
    lin = dp.weights(4, "linear")
    assert lin == sorted(lin) and lin[-1] > lin[0]           # newest (last) highest
    assert [round(x, 6) for x in lin] == [0.4, 0.8, 1.2, 1.6]
    assert dp.weights(3, None) == [1.0, 1.0, 1.0] and dp.weights(0, "linear") == []


def league(off, dfn, sched, mean=27.0, home=1.5):
    rows = []
    for gid, (date, h, a) in enumerate(sched, 1):
        rows += game(gid, date, h, a, mean + off[h] + dfn[a] + home, mean + off[a] + dfn[h] - home)
    return rows


def test_stage1_recovers_offense_defense_and_home_field():
    teams = list("ABCDEF")
    off = dict(zip(teams, [8, 4, 0, 0, -4, -8]))
    dfn = dict(zip(teams, [-6, 0, 3, -3, 0, 6]))
    sched = [(f"2025-09-{i % 28 + 1:02d}", h, a) for i, (h, a) in enumerate(list(itertools.permutations(teams, 2)) * 2)]
    fit = dp.stage1(league(off, dfn, sched), {t: (0.0, 0.0) for t in teams}, iterations=300)
    assert abs(fit["home"] - 1.5) < 0.05 and abs(fit["mean"] - 27) < 0.3
    for t in teams:   # shrinkage toward 0 priors is small with 20 games each
        assert abs(fit["off"][t] - off[t]) < 1.0 and abs(fit["def"][t] - dfn[t]) < 1.0


def test_clip_limits_a_single_blowout():
    rows = game(1, "2025-09-01", "A", "B", 98, 0) + game(2, "2025-09-08", "A", "C", 28, 27)
    fit = {"mean": 27.0, "home": 0.0, "off": {"B": 0.0, "C": 0.0}, "def": {"B": 0.0, "C": 0.0}, "prior": {"A": (0, 0)}}
    values = dp.game_values(rows, fit)
    assert max(v[2] for v in values["A"]) == dp.CLIP


def test_momentum_reacts_to_recent_change_and_standard_does_not_favor_order():
    # Team A: four poor games then four strong ones (adjusted offense -10 then +10); average opponent.
    values = {"A": [(f"2025-09-{i + 1:02d}", str(i), (-10 if i < 4 else 10), 0.0) for i in range(8)]}
    fit = {"prior": {"A": (0.0, 0.0)}, "off": {}, "def": {}}
    std = dp.model_ratings(values, fit, None)["A"][0]
    mom = dp.model_ratings(values, fit, "linear")["A"][0]
    assert abs(std) < 1e-9 and mom > 3     # equal weights cancel; stair-step tilts toward the recent form
    reversed_values = {"A": [(d, g, -o, 0.0) for d, g, o, _ in values["A"]]}
    assert dp.model_ratings(reversed_values, fit, "linear")["A"][0] < -3


def test_opponent_strength_enters_once():
    # A scores exactly what an average offense would against each opponent: adjusted value 0 regardless of schedule.
    fit = {"mean": 27.0, "home": 0.0, "off": {"S": 0.0, "W": 0.0}, "def": {"S": -10.0, "W": 10.0}, "prior": {"A": (0.0, 0.0)}}
    rows = game(1, "2025-09-01", "A", "S", 17, 27, neutral=True) + game(2, "2025-09-08", "A", "W", 37, 27, neutral=True)
    values = dp.game_values(rows, fit)
    assert [v[2] for v in values["A"]] == [0.0, 0.0]
    assert dp.model_ratings(values, fit, None)["A"] == (0.0, 0.0)


def test_projection_symmetry_and_probability():
    fit = {"mean": 27.0, "home": 1.5}
    ratings = {"A": (5.0, -2.0), "B": (5.0, -2.0), dp.FCS: (-10.0, 10.0)}
    hp, ap, m = dp.project("A", "B", True, ratings, fit)
    assert hp == ap and m == 0
    hp, ap, m = dp.project("A", "B", False, ratings, fit)
    assert abs(m - 3.0) < 1e-12 and abs(dp.probability(0, 12) - 0.5) < 1e-12
    assert dp.project("A", "Some FCS", False, ratings, fit)[2] > 20


def test_win_distribution_is_exact():
    dist = dp.win_distribution([0.5, 0.5])
    assert [round(x, 12) for x in dist] == [0.25, 0.5, 0.25]
    ps = [0.9, 0.3, 0.65, 0.5]
    d = dp.win_distribution(ps)
    assert abs(sum(d) - 1) < 1e-12 and abs(sum(k * q for k, q in enumerate(d)) - sum(ps)) < 1e-12


def test_fit_scale_recovers_known_scale():
    import random
    rng = random.Random(4)
    ms = [rng.uniform(-30, 30) for _ in range(3000)]
    ys = [int(rng.random() < 1 / (1 + math.exp(-m / 9))) for m in ms]
    assert abs(dp.fit_scale(ms, ys) - 9) < 1.2


def test_priors_regress_and_cover_new_teams():
    priors = dp.next_priors({"A": (10.0, -5.0), dp.FCS: (-10.0, 10.0)})
    assert priors == {"A": (6.0, -3.0)}
    fit = dp.stage1([], {"A": (6.0, -3.0), "New": dp.NEW_TEAM})
    assert dp.model_ratings({}, fit, "linear")["New"] == dp.NEW_TEAM     # no games: the prior
