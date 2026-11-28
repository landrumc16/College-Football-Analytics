"""Dynamic team strength research: leakage-free backtest of recency weighting.

Every prediction uses only games completed before that week (same-week games share one pregame snapshot).
The rating engine is the incumbent's iterative opponent-adjusted ridge model; the only change under test is a
per-(team, game) weight that depends on how recent the game is for that team. With all weights equal to 1 it
reproduces ratings.calculate_ratings exactly (asserted).

Data:
  2016-2025  research/archive/verified/espn-games.json.gz (verified results). Prior = previous season's final
             incumbent rating times a shrink factor (known before kickoff). One pseudo-conference (no verified
             historical conference map), identical for every method.
  2026       data/cfbd-2026-games.json with the production roster, conferences and preseason priors.
"""
import argparse
import gzip
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cfb_analytics.model import ModelSettings, adjusted_home_margin, win_probability_from_rating_gap  # noqa: E402
from cfb_analytics.ratings import Game, Team, calculate_ratings  # noqa: E402
from cfb_analytics.forecast_ledger import ALIASES  # noqa: E402

ARCHIVE = ROOT / "research/archive/verified/espn-games.json.gz"
CURRENT = ROOT / "data/cfbd-2026-games.json"
SETTINGS = ModelSettings()


# ---------------------------------------------------------------- weighted engine (incumbent when weights == 1)
def weighted_ratings(teams, games, weight_fn, settings=SETTINGS):
    """games: list of (order, Game). weight_fn(rank_from_latest, n_games) -> raw weight (normalized per team)."""
    by_name = {t.name: t for t in teams}
    conf_members = defaultdict(list)
    for t in teams:
        conf_members[t.conference].append(t.name)
    team_games = defaultdict(list)
    for idx, (order, g) in enumerate(games):
        for name in (g.home, g.away):
            if name in by_name:
                team_games[name].append((order, idx))
    weight = {}
    counts = defaultdict(float)
    for name, rows in team_games.items():
        rows.sort()
        n = len(rows)
        raw = [weight_fn(n - 1 - i, n) for i in range(n)]
        scale = n / sum(raw) if sum(raw) > 0 else 0.0     # mean weight 1: prior strength stays comparable
        for (order, idx), w in zip(rows, raw):
            weight[(name, idx)] = w * scale
            counts[name] += w * scale
    priors = {t.name: settings.prior_year_weight * t.prior for t in teams}
    passes = [priors]
    margins = [adjusted_home_margin(g.home_score, g.away_score, settings) for _, g in games]
    for _ in range(8):
        prev = passes[-1]
        contrib = defaultdict(float)
        for idx, (_, g) in enumerate(games):
            m = margins[idx]
            if g.home in by_name:
                contrib[g.home] += weight[(g.home, idx)] * (prev.get(g.away, settings.fcs_opponent_rating) + m)
            if g.away in by_name:
                contrib[g.away] += weight[(g.away, idx)] * (prev.get(g.home, settings.fcs_opponent_rating) - m)
        shift = {c: sum(prev[n] for n in names) / len(names) - sum(priors[n] for n in names) / len(names)
                 for c, names in conf_members.items()}
        passes.append({t.name: (contrib[t.name] + settings.ridge_strength *
                                (priors[t.name] + settings.conference_shrink * shift[t.conference])) /
                       (counts[t.name] + settings.ridge_strength) for t in teams})
    completed = len(games)
    chosen = 5 if completed < 200 else 6 if completed < 400 else 7 if completed < 650 else 8
    return passes[chosen]


# ---------------------------------------------------------------- recency methods
def incumbent(rank, n):
    return 1.0


def tiered(mid_weight, recent_weight, recent=3, mid=3):
    """Latest `recent` games share one equal weight; the next `mid` games share another; older games weight 1."""
    def fn(rank, n):
        return recent_weight if rank < recent else mid_weight if rank < recent + mid else 1.0
    fn.__name__ = f"tiered_r{recent}_m{mid}_{mid_weight:g}_{recent_weight:g}"
    return fn


def exponential(half_life):
    def fn(rank, n):
        return 0.5 ** (rank / half_life)
    fn.__name__ = f"exp_halflife_{half_life:g}"
    return fn


def window(size):
    def fn(rank, n):
        return 1.0 if rank < size else 0.15
    fn.__name__ = f"window_{size}"
    return fn


# ---------------------------------------------------------------- seasons
def historical_seasons(prior_shrink):
    data = json.loads(gzip.decompress(ARCHIVE.read_bytes()))
    seasons = {}
    prev_final = {}
    for season in sorted(data, key=int):
        rows = [g for g in data[season] if g["season_type"] in ("regular", "postseason") and g["fbs_participant"]
                and g["home_score"] is not None]
        fbs = sorted({g["home"] for g in rows if g["home_division"] == "FBS"} |
                     {g["away"] for g in rows if g["away_division"] == "FBS"})
        teams = [Team(t, "FBS", prior_shrink * prev_final.get(t, SETTINGS.new_team_rating)) for t in fbs]
        games = []
        for g in rows:
            if g["home_score"] == g["away_score"]:
                continue
            order = (1 if g["season_type"] == "postseason" else 0, g["week"], g["kickoff"])
            games.append({"order": order, "game": Game(g["home"], g["away"], g["home_score"], g["away_score"], g["week"]),
                          "neutral": bool(g["neutral_site"]), "id": g["game_id"]})
        games.sort(key=lambda r: r["order"])
        seasons[int(season)] = (teams, games)
        final = calculate_ratings(teams, [r["game"] for r in games])
        prev_final = {t: r.adaptive_rating for t, r in final.items()}
    return seasons


def season_2026():
    from cfb_analytics.parity import load_baseline
    roster, _ = load_baseline()
    teams = [Team(t["name"], t["conference"], t["prior"]) for t in roster]
    snap = json.loads(CURRENT.read_text())
    games = []
    for g in snap["games"]:
        if not g.get("completed") or g.get("home_score") is None or g["home_score"] == g["away_score"]:
            continue
        home, away = ALIASES.get(g["home"], g["home"]), ALIASES.get(g["away"], g["away"])
        games.append({"order": (0, g["week"], g.get("start_date") or ""), "neutral": bool(g.get("neutral_site")),
                      "game": Game(home, away, g["home_score"], g["away_score"], g["week"]), "id": str(g["game_id"])})
    games.sort(key=lambda r: r["order"])
    return teams, games


# ---------------------------------------------------------------- walk-forward evaluation
def walk_forward(teams, games, weight_fn, min_week_games=1):
    known = {t.name for t in teams}
    out = []
    keys = sorted({(r["order"][0], r["order"][1]) for r in games})
    for key in keys:
        history = [(r["order"], r["game"]) for r in games if (r["order"][0], r["order"][1]) < key]
        week_games = [r for r in games if (r["order"][0], r["order"][1]) == key]
        if not history:
            continue
        ratings = weighted_ratings(teams, history, weight_fn)
        for r in week_games:
            g = r["game"]
            if g.home not in known and g.away not in known:
                continue
            hr = ratings.get(g.home, SETTINGS.fcs_opponent_rating)
            ar = ratings.get(g.away, SETTINGS.fcs_opponent_rating)
            margin = hr - ar + (0.0 if r["neutral"] else SETTINGS.home_field_advantage)
            p = win_probability_from_rating_gap(margin, SETTINGS.win_probability_scale)
            out.append({"id": r["id"], "week": key, "pred": margin, "p": p, "actual": g.home_score - g.away_score,
                        "y": int(g.home_score > g.away_score), "home": g.home, "away": g.away,
                        "fbs_fbs": g.home in known and g.away in known})
    return out


def metrics(rows):
    n = len(rows)
    if not n:
        return None
    eps = 1e-15
    bins = [[] for _ in range(10)]
    for r in rows:
        bins[min(9, int(r["p"] * 10))].append(r)
    ece = sum(len(b) / n * abs(statistics.fmean(x["p"] for x in b) - statistics.fmean(x["y"] for x in b)) for b in bins if b)
    return {"games": n,
            "margin_mae": statistics.fmean(abs(r["pred"] - r["actual"]) for r in rows),
            "winner_accuracy": statistics.fmean((r["p"] >= 0.5) == bool(r["y"]) for r in rows),
            "brier": statistics.fmean((r["p"] - r["y"]) ** 2 for r in rows),
            "log_loss": -statistics.fmean(r["y"] * math.log(max(eps, r["p"])) + (1 - r["y"]) * math.log(max(eps, 1 - r["p"])) for r in rows),
            "calibration_ece": ece}


def paired_ci(a, b, key, seed=7, n=2000):
    """95% bootstrap interval of mean(b - a) on identical games, resampling weeks (clusters)."""
    by_week = defaultdict(list)
    amap = {r["id"]: r for r in a}
    for r in b:
        x = amap[r["id"]]
        if key == "brier":
            d = (r["p"] - r["y"]) ** 2 - (x["p"] - x["y"]) ** 2
        else:
            d = abs(r["pred"] - r["actual"]) - abs(x["pred"] - x["actual"])
        by_week[(r.get("season"), r["week"])].append(d)
    clusters = list(by_week.values())
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        sample = [d for _ in clusters for d in clusters[rng.randrange(len(clusters))]]
        means.append(statistics.fmean(sample))
    means.sort()
    total = [d for c in clusters for d in c]
    return round(statistics.fmean(total), 4), [round(means[int(0.025 * n)], 4), round(means[int(0.975 * n) - 1], 4)]


def run(methods, seasons):
    results = {}
    for m in methods:
        rows = []
        for season, (teams, games) in seasons.items():
            for r in walk_forward(teams, games, m):
                r["season"] = season
                rows.append(r)
        results[m.__name__] = rows
    return results


def form_adjusted(rows, k, n_form=3):
    """Current-form variant: add k * (home form - away form) to the incumbent margin. Form = mean of a team's last
    n_form residuals against the incumbent's own pregame margins (equal weights; known before kickoff)."""
    hist, out = defaultdict(list), []
    for season in sorted({r["season"] for r in rows}):
        srows = sorted((r for r in rows if r["season"] == season), key=lambda r: r["week"])
        for w in sorted({r["week"] for r in srows}):
            week = [r for r in srows if r["week"] == w]
            form = lambda t: sum(hist[(season, t)][-n_form:]) / n_form
            for r in week:
                adj = r["pred"] + k * (form(r["home"]) - form(r["away"]))
                out.append({**r, "pred": adj, "p": win_probability_from_rating_gap(adj, SETTINGS.win_probability_scale)})
            for r in week:
                res = r["actual"] - r["pred"]
                hist[(season, r["home"])].append(res)
                hist[(season, r["away"])].append(-res)
    return out


def momentum(rows):
    """Do teams that beat (or missed) the incumbent's forecasts over their last 3 games keep doing so next game?"""
    per = defaultdict(list)
    for r in rows:
        per[(r["season"], r["home"])].append((r["week"], r["actual"] - r["pred"]))
        per[(r["season"], r["away"])].append((r["week"], r["pred"] - r["actual"]))
    xs, ys, buckets = [], [], defaultdict(list)
    for lst in per.values():
        lst.sort()
        for j in range(3, len(lst)):
            recent = statistics.fmean(x for _, x in lst[j - 3:j])
            xs.append(recent); ys.append(lst[j][1])
            buckets["surging_gt_7" if recent > 7 else "slumping_lt_-7" if recent < -7 else "steady"].append(lst[j][1])
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return {"observations": len(xs), "slope_next_on_last3": round(slope, 3),
            "next_game_mean_residual": {b: {"n": len(v), "mean": round(statistics.fmean(v), 2)} for b, v in buckets.items()}}


TRAIN, TEST = (2017, 2018, 2019, 2021), (2022, 2023, 2024, 2025)   # 2020 excluded, as in the project's research


def study():
    shrinks = {}
    for shrink in (0.4, 0.6, 0.8, 0.9, 1.0):
        hs = historical_seasons(shrink)
        shrinks[shrink] = metrics(run([incumbent], {s: hs[s] for s in TRAIN})["incumbent"])["log_loss"]
    shrink = min(shrinks, key=shrinks.get)
    hist = historical_seasons(shrink)
    hist[2026] = season_2026()
    grid = [incumbent] + [tiered(a, b, 3, mid) for mid in (3, 4) for a in (1.0, 1.25, 1.5, 2.0)
                          for b in (1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0) if b >= a and (a, b) != (1.0, 1.0)]
    grid += [exponential(h) for h in (2, 3, 4, 6, 8, 12)] + [window(n) for n in (4, 6, 8)]
    train = run(grid, {s: hist[s] for s in TRAIN})
    train_m = {k: metrics(v) for k, v in train.items()}
    best = min((k for k in train_m if k.startswith("tiered")), key=lambda k: train_m[k]["log_loss"])
    chosen = {incumbent.__name__: incumbent}
    for fn in grid:
        if fn.__name__ in (best, "tiered_r3_m3_1_1.5", "tiered_r3_m3_2_3", "exp_halflife_4", "exp_halflife_12", "window_6"):
            chosen[fn.__name__] = fn
    evaluation = {}
    for label, years in (("heldout_2022_2025", TEST), ("season_2026", (2026,))):
        res = run(list(chosen.values()), {s: hist[s] for s in years})
        base = res["incumbent"]
        evaluation[label] = {k: {**{m: round(v, 4) for m, v in metrics(rows).items()},
                                 "delta_brier": paired_ci(base, rows, "brier"), "delta_mae": paired_ci(base, rows, "mae")}
                             for k, rows in res.items()}
        for kf in (0.05, 0.1):
            rows = form_adjusted(base, kf)
            evaluation[label][f"form_k{kf}"] = {**{m: round(v, 4) for m, v in metrics(rows).items()},
                                                "delta_brier": paired_ci(base, rows, "brier"), "delta_mae": paired_ci(base, rows, "mae")}
    form_train = {kf: round(metrics(form_adjusted(train["incumbent"], kf))["log_loss"], 4) for kf in (0.0, 0.05, 0.1, 0.15, 0.2, 0.3)}
    all_rows = run([incumbent], {s: hist[s] for s in TRAIN + TEST + (2026,)})["incumbent"]
    tt = [{"week": r["week"][1], "opponent": r["away"] if r["home"] == "Texas Tech" else r["home"],
           "predicted_tt_margin": round(r["pred"] if r["home"] == "Texas Tech" else -r["pred"], 1),
           "actual_tt_margin": r["actual"] if r["home"] == "Texas Tech" else -r["actual"]}
          for r in all_rows if r["season"] == 2026 and "Texas Tech" in (r["home"], r["away"])]
    return {"prior_shrink_train_log_loss": shrinks, "prior_shrink": shrink, "train_seasons": TRAIN, "test_seasons": TEST,
            "train_top10_by_log_loss": sorted(((round(m["log_loss"], 4), round(m["margin_mae"], 3), k) for k, m in train_m.items()))[:10],
            "train_incumbent": {m: round(v, 4) for m, v in train_m["incumbent"].items()}, "preregistered_tiered": best,
            "form_k_train_log_loss": form_train, "evaluation": evaluation, "momentum": momentum(all_rows),
            "texas_tech_2026": tt}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output", type=Path, help="write the full study as JSON")
    args = ap.parse_args(argv)
    teams, games = season_2026()
    hist = [(r["order"], r["game"]) for r in games]
    inc = calculate_ratings(teams, [g for _, g in hist])
    mine = weighted_ratings(teams, hist, incumbent)
    assert max(abs(inc[t].adaptive_rating - mine[t]) for t in mine) < 1e-9, "weighted engine must equal incumbent"
    result = study()
    text = json.dumps(result, indent=1, sort_keys=True, default=list) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text if not args.output else f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
