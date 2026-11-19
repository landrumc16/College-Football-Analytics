"""V8 M4-M6: matchup features, challenger forecast model and pre-registered walk-forward evaluation.

Research only: never changes published forecasts. Every feature for a game comes from games strictly before
that game's week. The historical baseline is a labelled retrospective replay of the incumbent's own rating
method (cfb_analytics.ratings), not an archived forecast. Protocol: research/v8/evaluation-protocol.json.

  python -m cfb_analytics.v8_challenger            # writes research/v8/challenger-evaluation.json
"""
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from . import v8_stats as st
from .model import ModelSettings, win_probability_from_rating_gap
from .ratings import Game, Team, calculate_ratings

ROOT = Path("research/v8")
SETTINGS = ModelSettings()
TARGET_SEASONS = list(range(2017, 2026))
MIN_PRIOR_GAMES = 3

# Matchup feature groups: (metric, offense higher is better). Each becomes
# expected(home offense vs away defense) - expected(away offense vs home defense), oriented so + favours home.
GROUPS = {
    "efficiency": ["epa", "sr"],
    "scoring": ["ppd"],
    "rush_pass": ["rush_sr", "pass_sr", "rush_ypc", "pass_ypd"],
    "explosive": ["expl", "rush_expl", "pass_expl"],
    "situational": ["third", "rz_td", "sack", "to"],
}
VULNERABILITY = ["rush_sr", "pass_sr", "pass_expl", "sack"]
FIT_METRICS = sorted({m for ms in GROUPS.values() for m in ms} | set(VULNERABILITY))
EXTRA_GROUPS = ["trend", "volatility", "vulnerability_interactions", "rest"]
ALL_GROUPS = list(GROUPS) + EXTRA_GROUPS


# ---------------------------------------------------------------- schedule and baseline replay

def season_games(rows):
    """One record per completed game involving an FBS team, ordered, with a global week index."""
    reg_max = max((r["week"] for r in rows if r["season_type"] == "regular"), default=0)
    games = {}
    for r in rows:
        if r["game_id"] in games or r["site"] == "away":
            continue
        idx = r["week"] if r["season_type"] == "regular" else reg_max + (r["week"] or 1)
        games[r["game_id"]] = {"game_id": r["game_id"], "week": idx, "date": r["date"], "home": r["team"],
                               "away": r["opp"], "neutral": r["site"] == "neutral", "home_score": r["pf"],
                               "away_score": r["pa"], "home_fbs": r["team_fbs"], "away_fbs": r["opp_fbs"],
                               "home_conf": r["team_conf"], "away_conf": r["opp_conf"]}
    return sorted(games.values(), key=lambda g: (g["week"], g["date"] or "", g["game_id"]))


def replay_incumbent(rows, season, priors):
    """Week-by-week incumbent ratings with given priors. Returns ({game_id: home gap}, final ratings)."""
    games = season_games(rows)
    conf = {r["team"]: r["team_conf"] or "FBS" for r in rows if r["team_fbs"]}
    teams = [Team(t, conf[t], priors.get(t, SETTINGS.new_team_rating)) for t in sorted(conf)]
    known = set(conf)
    gaps, history = {}, []
    for week in sorted({g["week"] for g in games}):
        ratings = calculate_ratings(teams, history, SETTINGS)
        for g in (x for x in games if x["week"] == week):
            h = ratings[g["home"]].adaptive_rating if g["home"] in known else SETTINGS.fcs_opponent_rating
            a = ratings[g["away"]].adaptive_rating if g["away"] in known else SETTINGS.fcs_opponent_rating
            gaps[g["game_id"]] = h - a + (0.0 if g["neutral"] else SETTINGS.home_field_advantage)
        history += [Game(g["home"], g["away"], g["home_score"], g["away_score"], g["week"])
                    for g in games if g["week"] == week and g["home_score"] != g["away_score"]]
    final = calculate_ratings(teams, history, SETTINGS)
    return gaps, {t: r.adaptive_rating for t, r in final.items()}


# ---------------------------------------------------------------- as-of matchup features

def snapshot(rows, cutoff):
    """Opponent-adjusted fits and per-team context from games strictly before cutoff."""
    prior_rows = st.before(rows, cutoff)
    units = st.pair_units(prior_rows)
    fits = {m: st.adjust(units, m, iterations=80) for m in FIT_METRICS}
    mine = defaultdict(list)
    for u in units:
        if u[5]["team_fbs"] and u[5]["opp_fbs"]:
            mine[u[0]].append(u)
    for t in mine:
        mine[t].sort(key=lambda u: (u[5]["date"] or "", u[5]["game_id"]))
    last_date = {}
    for r in prior_rows:
        last_date[r["team"]] = max(last_date.get(r["team"], ""), r["date"] or "")
    context = {}
    for t, us in mine.items():
        values = []
        for u in us:
            o = st.game_adjusted(u, "epa", fits["epa"], "off")
            d = st.game_adjusted(u, "epa", fits["epa"], "def")
            if o is not None and d is not None:
                values.append(o - d)
        mean, sd = st.mean_sd(values)
        recent = sum(values[-4:]) / len(values[-4:]) if len(values) >= 6 else None
        context[t] = {"games": len(us), "trend": (recent - mean) if recent is not None else 0.0,
                      "vol": sd if sd is not None and len(values) >= st.MIN_GAMES_VOLATILITY else None}
    zs = {}
    for m in VULNERABILITY:
        f = fits[m]
        if not f:
            continue
        sign = 1 if st.METRICS[m][3] else -1
        offs = [sign * v for v in f["off"].values()]
        defs = [sign * v for v in f["def"].values()]
        so = math.sqrt(sum(v * v for v in offs) / len(offs)) or 1.0
        sd_ = math.sqrt(sum(v * v for v in defs) / len(defs)) or 1.0
        zs[m] = ({t: sign * v / so for t, v in f["off"].items()}, {t: sign * v / sd_ for t, v in f["def"].items()})
    return {"fits": fits, "context": context, "z": zs, "last_date": last_date}


def days_between(a, b):
    from datetime import date
    if not a or not b:
        return None
    return (date.fromisoformat(b[:10]) - date.fromisoformat(a[:10])).days


def features(game, snap, gap):
    """Feature dict for one game (home perspective) or None if either team lacks enough prior play data."""
    h, a = game["home"], game["away"]
    ctx = snap["context"]
    if ctx.get(h, {}).get("games", 0) < MIN_PRIOR_GAMES or ctx.get(a, {}).get("games", 0) < MIN_PRIOR_GAMES:
        return None
    x = {"gap": gap}
    for group, metrics in GROUPS.items():
        for m in metrics:
            f = snap["fits"][m]
            if not f or h not in f["off"] or a not in f["off"]:
                return None
            sign = 1 if st.METRICS[m][3] else -1
            home_exp = f["off"][h] + f["def"][a]
            away_exp = f["off"][a] + f["def"][h]
            x[f"{group}:{m}"] = sign * (home_exp - away_exp)
    x["trend:epa_last4"] = ctx[h]["trend"] - ctx[a]["trend"]
    vh, va = ctx[h]["vol"], ctx[a]["vol"]
    x["volatility:epa_sd"] = (vh - va) if vh is not None and va is not None else 0.0
    for m in VULNERABILITY:
        if m not in snap["z"]:
            continue
        zo, zd = snap["z"][m]
        x[f"vulnerability_interactions:{m}"] = zo.get(h, 0) * zd.get(a, 0) - zo.get(a, 0) * zd.get(h, 0)
    rest_h = days_between(snap["last_date"].get(h), game["date"])
    rest_a = days_between(snap["last_date"].get(a), game["date"])
    clip = lambda d: min(max(d, 3), 14) if d is not None else 7
    x["rest:days"] = clip(rest_h) - clip(rest_a)
    x["rest:short_week"] = (clip(rest_h) <= 5) - (clip(rest_a) <= 5)
    return x


# ---------------------------------------------------------------- model

def solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        if abs(m[col][col]) < 1e-12:
            continue
        for r in range(n):
            if r != col:
                factor = m[r][col] / m[col][col]
                for c in range(col, n + 1):
                    m[r][c] -= factor * m[col][c]
    return [m[i][n] / m[i][i] if abs(m[i][i]) > 1e-12 else 0.0 for i in range(n)]


class Ridge:
    def __init__(self, keys, l2=25.0):
        self.keys, self.l2 = keys, l2

    def fit(self, xs, ys):
        k = len(self.keys)
        self.mu = [sum(x[key] for x in xs) / len(xs) for key in self.keys]
        self.sd = [math.sqrt(sum((x[key] - self.mu[i]) ** 2 for x in xs) / len(xs)) or 1.0 for i, key in enumerate(self.keys)]
        z = [[(x[key] - self.mu[i]) / self.sd[i] for i, key in enumerate(self.keys)] for x in xs]
        ybar = sum(ys) / len(ys)
        ata = [[sum(r[i] * r[j] for r in z) + (self.l2 if i == j else 0.0) for j in range(k)] for i in range(k)]
        aty = [sum(r[i] * (y - ybar) for r, y in zip(z, ys)) for i in range(k)]
        self.beta, self.b0 = solve(ata, aty), ybar
        preds = [self.margin(x) for x in xs]
        self.scale = fit_scale(preds, [int(y > 0) for y in ys])
        return self

    def margin(self, x):
        return self.b0 + sum(b * (x[key] - self.mu[i]) / self.sd[i] for i, (b, key) in enumerate(zip(self.beta, self.keys)))

    def prob(self, x):
        return 1 / (1 + math.exp(-self.margin(x) / self.scale))

    def coefficients(self):
        return {key: round(b / s, 5) for key, b, s in zip(self.keys, self.beta, self.sd)}


def fit_scale(margins, outcomes):
    """Logistic scale s minimising training log loss for p = 1/(1+exp(-margin/s)) (golden-section search)."""
    def loss(s):
        total = 0.0
        for m, y in zip(margins, outcomes):
            p = min(max(1 / (1 + math.exp(-m / s)), 1e-6), 1 - 1e-6)
            total -= y * math.log(p) + (1 - y) * math.log(1 - p)
        return total
    lo, hi = 2.0, 40.0
    for _ in range(60):
        m1, m2 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
        if loss(m1) < loss(m2):
            hi = m2
        else:
            lo = m1
    return (lo + hi) / 2


# ---------------------------------------------------------------- metrics

def score(probs, outcomes):
    n = len(probs)
    if not n:
        return None
    clip = [min(max(p, 1e-6), 1 - 1e-6) for p in probs]
    return {"games": n, "brier": sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / n,
            "log_loss": -sum(y * math.log(p) + (1 - y) * math.log(1 - p) for p, y in zip(clip, outcomes)) / n,
            "winner_accuracy": sum((p >= 0.5) == bool(y) for p, y in zip(probs, outcomes)) / n,
            "calibration_slope": calibration_slope(probs, outcomes)}


def calibration_slope(probs, outcomes):
    """Slope of a one-variable logistic fit of outcome on logit(p) (1 = perfectly scaled)."""
    xs = [math.log(min(max(p, 1e-6), 1 - 1e-6) / (1 - min(max(p, 1e-6), 1 - 1e-6))) for p in probs]
    a, b = 0.0, 1.0
    for _ in range(50):  # Newton steps
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in zip(xs, outcomes):
            p = 1 / (1 + math.exp(-(a + b * x)))
            w = p * (1 - p)
            g0 += y - p; g1 += (y - p) * x
            h00 += w; h01 += w * x; h11 += w * x * x
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        a += (h11 * g0 - h01 * g1) / det
        b += (-h01 * g0 + h00 * g1) / det
    return b


def calibration_bins(probs, outcomes, bins=10):
    out = []
    for i in range(bins):
        sel = [(p, y) for p, y in zip(probs, outcomes) if i / bins <= p < (i + 1) / bins or (i == bins - 1 and p == 1)]
        if sel:
            out.append({"bin": f"{i / bins:.1f}-{(i + 1) / bins:.1f}", "games": len(sel),
                        "mean_forecast": round(sum(p for p, _ in sel) / len(sel), 4),
                        "observed": round(sum(y for _, y in sel) / len(sel), 4)})
    return out


def clustered_bootstrap(records, a_key, b_key, draws=2000, seed=8):
    """CI95 of mean Brier(a) - Brier(b), resampling season-week clusters."""
    clusters = defaultdict(list)
    for r in records:
        clusters[(r["season"], r["week"])].append(((r[a_key] - r["y"]) ** 2) - ((r[b_key] - r["y"]) ** 2))
    keys = sorted(clusters)
    rng = random.Random(seed)
    stats = []
    for _ in range(draws):
        total = count = 0
        for _k in keys:
            c = clusters[keys[rng.randrange(len(keys))]]
            total += sum(c); count += len(c)
        stats.append(total / count)
    stats.sort()
    return [round(stats[int(0.025 * draws)], 5), round(stats[int(0.975 * draws) - 1], 5)]


# ---------------------------------------------------------------- walk-forward evaluation

def build_records(seasons, load=st.load_rows):
    """Per-game feature records for every season (baseline gap from the incumbent replay)."""
    records, priors = [], {}
    for season in seasons:
        rows = load(season)
        gaps, final = replay_incumbent(rows, season, priors)
        priors = final
        games = season_games(rows)
        for week in sorted({g["week"] for g in games}):
            week_games = [g for g in games if g["week"] == week and g["home_fbs"] and g["away_fbs"]
                          and g["home_score"] != g["away_score"]]
            if not week_games:
                continue
            cutoff = min(g["date"] for g in week_games)[:10]
            snap = snapshot(rows, cutoff)
            for g in week_games:
                x = features(g, snap, gaps[g["game_id"]])
                if x is None:
                    continue
                records.append({"season": season, "week": week, "game_id": g["game_id"], "home": g["home"],
                                "away": g["away"], "margin": g["home_score"] - g["away_score"],
                                "y": int(g["home_score"] > g["away_score"]), "x": x,
                                "home_power": st.is_power(g["home"], g["home_conf"], season),
                                "away_power": st.is_power(g["away"], g["away_conf"], season)})
        print(f"{season}: {sum(r['season'] == season for r in records)} eligible games")
    return records


def keys_for(groups):
    return ["gap"] + [k for g in groups for k in sorted(KEYS_BY_GROUP[g])]


KEYS_BY_GROUP = {g: {f"{g}:{m}" for m in ms} for g, ms in GROUPS.items()}
KEYS_BY_GROUP.update({"trend": {"trend:epa_last4"}, "volatility": {"volatility:epa_sd"},
                      "vulnerability_interactions": {f"vulnerability_interactions:{m}" for m in VULNERABILITY},
                      "rest": {"rest:days", "rest:short_week"}})


def walk_forward(records, groups, targets=TARGET_SEASONS):
    """Challenger probabilities/margins for each target season, trained only on earlier seasons (2020 excluded from training)."""
    keys = keys_for(groups)
    out = {}
    for season in targets:
        train = [r for r in records if r["season"] < season and r["season"] != 2020]
        if len(train) < 200:
            continue
        model = Ridge(keys).fit([r["x"] for r in train], [r["margin"] for r in train])
        for r in records:
            if r["season"] == season:
                out[r["game_id"]] = (model.prob(r["x"]), model.margin(r["x"]))
    return out


def evaluate(records, groups=ALL_GROUPS):
    pred = walk_forward(records, groups)
    rows = [dict(r, c=pred[r["game_id"]][0], cm=pred[r["game_id"]][1],
                 b=win_probability_from_rating_gap(r["x"]["gap"], SETTINGS.win_probability_scale), bm=r["x"]["gap"])
            for r in records if r["game_id"] in pred]
    return rows


def summary(rows):
    def both(sel):
        return {"games": len(sel),
                "challenger": score([r["c"] for r in sel], [r["y"] for r in sel]),
                "baseline": score([r["b"] for r in sel], [r["y"] for r in sel]),
                "margin_mae": {"challenger": round(sum(abs(r["cm"] - r["margin"]) for r in sel) / len(sel), 3),
                               "baseline": round(sum(abs(r["bm"] - r["margin"]) for r in sel) / len(sel), 3)} if sel else None}
    pooled = [r for r in rows if r["season"] != 2020]
    by_season = {s: both([r for r in rows if r["season"] == s]) for s in sorted({r["season"] for r in rows})}
    weeks = sorted({r["week"] for r in rows})
    return {"pooled_non2020": both(pooled),
            "brier_difference_ci95": clustered_bootstrap(pooled, "c", "b"),
            "by_season": by_season,
            "early_weeks_le_6": both([r for r in pooled if r["week"] <= 6]),
            "late_weeks_ge_7": both([r for r in pooled if r["week"] >= 7]),
            "both_power": both([r for r in pooled if r["home_power"] and r["away_power"]]),
            "other_games": both([r for r in pooled if not (r["home_power"] and r["away_power"])]),
            "calibration_bins": {"challenger": calibration_bins([r["c"] for r in pooled], [r["y"] for r in pooled]),
                                 "baseline": calibration_bins([r["b"] for r in pooled], [r["y"] for r in pooled])}}


def gates(result, ablation):
    pooled = result["pooled_non2020"]
    c, b = pooled["challenger"]["brier"], pooled["baseline"]["brier"]
    improved = sum(v["challenger"]["brier"] < v["baseline"]["brier"] for s, v in result["by_season"].items() if s != 2020)
    seasons = sum(1 for s in result["by_season"] if s != 2020)
    checks = {
        "pooled_relative_brier_improvement": {"value": round((b - c) / b, 4), "required": ">= 0.02", "pass": (b - c) / b >= 0.02},
        "brier_ci95_upper_below_zero": {"value": result["brier_difference_ci95"][1], "required": "< 0", "pass": result["brier_difference_ci95"][1] < 0},
        "seasons_improved": {"value": f"{improved} of {seasons}", "required": ">= 6 of 8", "pass": improved >= 6},
        "log_loss_not_worse": {"value": round(pooled["challenger"]["log_loss"] - pooled["baseline"]["log_loss"], 5), "required": "<= 0",
                               "pass": pooled["challenger"]["log_loss"] <= pooled["baseline"]["log_loss"]},
        "calibration_slope": {"value": round(pooled["challenger"]["calibration_slope"], 3), "required": "0.9-1.1",
                              "pass": 0.9 <= pooled["challenger"]["calibration_slope"] <= 1.1},
    }
    return checks


def ablation(records):
    full = evaluate(records)
    base = sum((r["c"] - r["y"]) ** 2 for r in full if r["season"] != 2020) / sum(r["season"] != 2020 for r in full)
    out = {}
    for group in ALL_GROUPS:
        rows = evaluate(records, [g for g in ALL_GROUPS if g != group])
        brier = sum((r["c"] - r["y"]) ** 2 for r in rows if r["season"] != 2020) / sum(r["season"] != 2020 for r in rows)
        out[group] = {"brier_without": round(brier, 5), "brier_with_all": round(base, 5),
                      "helps": brier > base, "change_if_removed": round(brier - base, 5)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2016-2025")
    ap.add_argument("--out", type=Path, default=ROOT / "challenger-evaluation.json")
    args = ap.parse_args(argv)
    first, _, last = args.seasons.partition("-")
    records = build_records(list(range(int(first), int(last) + 1)))
    rows = evaluate(records)
    result = summary(rows)
    abl = ablation(records)
    kept = [g for g in ALL_GROUPS if abl[g]["helps"]]
    reduced = summary(evaluate(records, kept)) if kept != ALL_GROUPS else result
    final = {"protocol": "research/v8/evaluation-protocol.json", "kind": "retrospective walk-forward replay; not archived forecasts",
             "all_groups": result, "ablation": abl, "kept_groups": kept, "reduced_model": reduced,
             "gates_all_groups": gates(result, abl), "gates_reduced": gates(reduced, abl)}
    keys = keys_for(kept)
    model = Ridge(keys).fit([r["x"] for r in records if r["season"] != 2020], [r["margin"] for r in records if r["season"] != 2020])
    final["final_model"] = {"groups": kept, "coefficients_per_unit": model.coefficients(), "intercept": round(model.b0, 4),
                            "probability_scale": round(model.scale, 4), "training_games": sum(r["season"] != 2020 for r in records)}
    args.out.write_text(json.dumps(final, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: final[k] for k in ("gates_all_groups", "gates_reduced", "kept_groups")}, indent=1))


if __name__ == "__main__":
    main()
