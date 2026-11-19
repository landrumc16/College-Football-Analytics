"""Walk-forward evaluation of the Standard and Momentum models against the incumbent method.

Every projection for a game uses only games strictly before that game's week. The incumbent comparison is the
labelled retrospective replay of the incumbent rating method used in V8 (prior = previous season's final rating),
plus the authentic published 2026 incumbent probabilities where they exist. Season-record accuracy uses retrospective
mid-season snapshots (as of the first game of week 8), not archived forecasts.

  python -m cfb_analytics.dual_evaluation        # writes research/dual/evaluation.json
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from . import dual_projection as dp
from . import v8_stats as st
from .model import ModelSettings, win_probability_from_rating_gap
from .ratings import Game, Team, calculate_ratings
from .v8_challenger import calibration_bins, calibration_slope, clustered_bootstrap, replay_incumbent, score, season_games

OUT = Path("research/dual/evaluation.json")
SETTINGS = ModelSettings()
SELECT_SEASONS = [2017, 2018, 2019, 2021]
TEST_SEASONS = [2022, 2023, 2024, 2025]
SNAPSHOT_WEEK = 8


def season_priors(rows, previous):
    teams = {r["team"] for r in rows if r["team_fbs"]}
    return {t: previous.get(t, dp.NEW_TEAM) for t in teams}


def incumbent_snapshot_probabilities(rows, inc_priors, cutoff, remaining):
    conf = {r["team"]: r["team_conf"] or "FBS" for r in rows if r["team_fbs"]}
    teams = [Team(t, conf[t], inc_priors.get(t, SETTINGS.new_team_rating)) for t in sorted(conf)]
    history = [Game(g["home"], g["away"], g["home_score"], g["away_score"], g["week"])
               for g in season_games(st.before(rows, cutoff)) if g["home_score"] != g["away_score"]]
    ratings = calculate_ratings(teams, history, SETTINGS)
    rating = lambda t: ratings[t].adaptive_rating if t in ratings else SETTINGS.fcs_opponent_rating
    return {g["game_id"]: win_probability_from_rating_gap(rating(g["home"]) - rating(g["away"]) + (0 if g["neutral"] else SETTINGS.home_field_advantage),
                                                          SETTINGS.win_probability_scale) for g in remaining}


def evaluate_season(season, rows, priors, inc_priors):
    """Per-game records, the season's final Standard ratings, incumbent final ratings and a mid-season record snapshot."""
    full_priors = season_priors(rows, priors)
    gaps, inc_final = replay_incumbent(rows, season, inc_priors)
    games = season_games(rows)
    records = []
    snapshot = None
    for week in sorted({g["week"] for g in games}):
        week_games = [g for g in games if g["week"] == week]
        cutoff = min(g["date"] for g in week_games)[:10]
        prior_rows = st.before(rows, cutoff)
        fit = dp.stage1(prior_rows, full_priors)
        values = dp.game_values(prior_rows, fit)
        ratings = {k: dp.model_ratings(values, fit, kind) for k, (_, kind) in dp.WEIGHTINGS.items()}
        for g in week_games:
            if not (g["home_fbs"] and g["away_fbs"]) or g["home_score"] == g["away_score"]:
                continue
            models = {}
            for k in dp.WEIGHTINGS:
                hp, ap, m = dp.project(g["home"], g["away"], g["neutral"], ratings[k], fit)
                models[k] = [round(hp, 3), round(ap, 3), round(m, 3)]
            records.append({"season": season, "week": week, "game_id": g["game_id"], "home": g["home"], "away": g["away"],
                            "y": int(g["home_score"] > g["away_score"]), "margin": g["home_score"] - g["away_score"],
                            "home_points": g["home_score"], "away_points": g["away_score"],
                            "models": models, "incumbent_gap": round(gaps[g["game_id"]], 3)})
        if snapshot is None and week >= SNAPSHOT_WEEK:
            regular = [g for g in games if g["date"][:10] >= cutoff and season_type(rows, g) == "regular"]
            fbs = sorted({r["team"] for r in rows if r["team_fbs"]})
            done = defaultdict(int)
            final = defaultdict(int)
            for g in games:
                if season_type(rows, g) != "regular" or g["home_score"] == g["away_score"]:
                    continue
                winner = g["home"] if g["home_score"] > g["away_score"] else g["away"]
                final[winner] += 1
                if g["date"][:10] < cutoff:
                    done[winner] += 1
            inc_p = incumbent_snapshot_probabilities(rows, inc_priors, cutoff, regular)
            snapshot = {"cutoff": cutoff, "teams": {}}
            for t in fbs:
                entry = {"completed_wins": done[t], "actual_final_wins": final[t]}
                # Remaining-game margins from this team's side; probabilities need each season's walk-forward scale.
                entry["margins"] = {k: [m if t == g["home"] else -m
                                        for g in regular if t in (g["home"], g["away"])
                                        for _, _, m in [dp.project(g["home"], g["away"], g["neutral"], ratings[k], fit)]]
                                    for k in dp.WEIGHTINGS}
                entry["incumbent"] = done[t] + sum((inc_p[g["game_id"]] if t == g["home"] else 1 - inc_p[g["game_id"]]) for g in regular if t in (g["home"], g["away"]))
                snapshot["teams"][t] = entry
    fit = dp.stage1(rows, full_priors)
    final_std = dp.model_ratings(dp.game_values(rows, fit), fit, None)
    return records, dp.next_priors(final_std), inc_final, snapshot


_types = {}


def season_type(rows, game):
    key = id(rows)
    if key not in _types:
        _types[key] = {r["game_id"]: r["season_type"] for r in rows}
    return _types[key][game["game_id"]]


def scales_by_season(records, kind, seasons):
    """Walk-forward logistic scale for each target season, fitted on earlier non-2020 seasons."""
    out = {}
    for s in seasons:
        train = [r for r in records if r["season"] < s and r["season"] != 2020]
        out[s] = dp.fit_scale([r["models"][kind][2] for r in train], [r["y"] for r in train]) if len(train) >= 200 else None
    return out


def summarise(records, kinds, seasons):
    scales = {k: scales_by_season(records, k, seasons) for k in kinds}
    rows = []
    for r in records:
        if r["season"] not in seasons or any(scales[k][r["season"]] is None for k in kinds):
            continue
        row = {"season": r["season"], "week": r["week"], "y": r["y"], "margin": r["margin"],
               "total": r["home_points"] + r["away_points"], "home_points": r["home_points"], "away_points": r["away_points"],
               "incumbent": win_probability_from_rating_gap(r["incumbent_gap"], SETTINGS.win_probability_scale), "incumbent_margin": r["incumbent_gap"]}
        for k in kinds:
            hp, ap, m = r["models"][k]
            row[k] = dp.probability(m, scales[k][r["season"]])
            row[k + "_margin"], row[k + "_hp"], row[k + "_ap"] = m, hp, ap
        rows.append(row)
    return rows, scales


def block(rows, kinds):
    if not rows:
        return None
    ys = [r["y"] for r in rows]
    out = {"games": len(rows), "incumbent_replay": score([r["incumbent"] for r in rows], ys)}
    out["incumbent_replay"]["margin_mae"] = sum(abs(r["incumbent_margin"] - r["margin"]) for r in rows) / len(rows)
    for k in kinds:
        out[k] = score([r[k] for r in rows], ys)
        out[k]["margin_mae"] = sum(abs(r[k + "_margin"] - r["margin"]) for r in rows) / len(rows)
        out[k]["score_mae"] = sum(abs(r[k + "_hp"] - r["home_points"]) + abs(r[k + "_ap"] - r["away_points"]) for r in rows) / (2 * len(rows))
        out[k]["total_mae"] = sum(abs(r[k + "_hp"] + r[k + "_ap"] - r["total"]) for r in rows) / len(rows)
    return out


def round_tree(x):
    if isinstance(x, float):
        return round(x, 5)
    if isinstance(x, dict):
        return {k: round_tree(v) for k, v in x.items()}
    if isinstance(x, list):
        return [round_tree(v) for v in x]
    return x


def record_accuracy(snapshots, kinds, scales):
    out = {}
    for k in kinds + ["incumbent"]:
        errs = []
        for season, snap in snapshots.items():
            if season == 2020 or not snap or scales["standard"].get(season) is None:   # identical seasons for every model
                continue
            for t, e in snap["teams"].items():
                if k == "incumbent":
                    exp = e["incumbent"]
                else:
                    exp = e["completed_wins"] + sum(dp.probability(m, scales[k][season]) for m in e["margins"][k])
                errs.append(exp - e["actual_final_wins"])
        out[k] = {"teams": len(errs), "mae_wins": sum(abs(e) for e in errs) / len(errs) if errs else None,
                  "rmse_wins": math.sqrt(sum(e * e for e in errs) / len(errs)) if errs else None}
    return out


def authentic_2026(records, kinds, path=Path("data/pregame-2026-history.json")):
    published = json.loads(path.read_text())
    out_rows = []
    scale = {k: dp.fit_scale([r["models"][k][2] for r in records if r["season"] < 2026 and r["season"] != 2020],
                             [r["y"] for r in records if r["season"] < 2026 and r["season"] != 2020]) for k in kinds}
    for r in records:
        f = published.get(r["game_id"])
        if r["season"] != 2026 or not f or f.get("source") != "generated_before_kickoff" or f.get("home") != r["home"]:
            continue
        row = {"season": 2026, "week": r["week"], "y": r["y"], "published": f["home_win_probability"],
               "replay": win_probability_from_rating_gap(r["incumbent_gap"], SETTINGS.win_probability_scale)}
        for k in kinds:
            row[k] = dp.probability(r["models"][k][2], scale[k])
        out_rows.append(row)
    if not out_rows:
        return None
    ys = [r["y"] for r in out_rows]
    res = {"games": len(out_rows), "kind": "incumbent probabilities recorded before kickoff; dual models computed from pre-week data",
           "published_incumbent": score([r["published"] for r in out_rows], ys), "incumbent_replay": score([r["replay"] for r in out_rows], ys)}
    for k in kinds:
        res[k] = score([r[k] for r in out_rows], ys)
        res[k + "_minus_published_ci95"] = clustered_bootstrap(out_rows, k, "published")
    return res


PRIOR_GRID = [(regress, games) for regress in (0.6, 0.7, 0.8, 0.9, 1.0) for games in (2.0, 3.0, 5.0)]


def tune_priors():
    """Choose the preseason-prior settings by Standard-model Brier on the selection seasons only."""
    results = []
    for regress, games in PRIOR_GRID:
        dp.REGRESS, dp.PRIOR_GAMES = regress, games
        records, _ = run(range(2016, 2022), quiet=True)
        rows, _ = summarise(records, ["standard"], SELECT_SEASONS)
        brier = sum((r["standard"] - r["y"]) ** 2 for r in rows) / len(rows)
        results.append({"regress": regress, "prior_games": games, "selection_brier": round(brier, 5)})
    best = min(results, key=lambda r: r["selection_brier"])
    dp.REGRESS, dp.PRIOR_GAMES = best["regress"], best["prior_games"]
    return results, best


def run(seasons=range(2016, 2027), quiet=False):
    records, snapshots = [], {}
    priors, inc_priors = {}, {}
    for season in seasons:
        rows = st.load_rows(season)
        recs, priors, inc_priors, snap = evaluate_season(season, rows, priors, inc_priors)
        records += recs
        snapshots[season] = snap
        if not quiet:
            print(f"{season}: {len(recs)} FBS games")
    return records, snapshots


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    grid, best = tune_priors()
    print("prior tuning (selection seasons only):", grid, "->", best)
    records, snapshots = run()
    hist = [r for r in records if r["season"] <= 2025]
    kinds = list(dp.WEIGHTINGS)
    targets = sorted({r["season"] for r in hist if r["season"] >= 2017})
    rows, scales = summarise(hist, kinds, targets)
    pooled = [r for r in rows if r["season"] != 2020]
    momentum = [k for k in kinds if k != "standard"]
    select_rows = [r for r in pooled if r["season"] in SELECT_SEASONS]
    selected = min(momentum, key=lambda k: sum((r[k] - r["y"]) ** 2 for r in select_rows) / len(select_rows))
    test_rows = [r for r in pooled if r["season"] in TEST_SEASONS]
    result = {
        "protocol": {"cohort": "FBS vs FBS completed non-tied games, 2017-2025 (2020 reported but excluded from pooled results)",
                     "as_of": "every projection uses games strictly before the game's week",
                     "incumbent": "retrospective replay of the incumbent rating method (prior = previous season's final rating); not archived forecasts",
                     "momentum_selection": f"decay chosen by pooled Brier on {SELECT_SEASONS}; reported untouched on {TEST_SEASONS}",
                     "season_records": f"retrospective snapshot as of week {SNAPSHOT_WEEK} versus actual final regular-season wins",
                     "parameters": {"clip_points": dp.CLIP, "prior_games": dp.PRIOR_GAMES, "stage1_prior_games": dp.STAGE1_PRIOR, "regress": dp.REGRESS}},
        "selected_momentum": selected,
        "prior_tuning": {"grid": grid, "chosen": best, "seasons": SELECT_SEASONS},
        "weightings": {k: label for k, (label, _) in dp.WEIGHTINGS.items()},
        "pooled_2017_2025": block(pooled, kinds),
        "selection_seasons": block(select_rows, kinds),
        "test_seasons_2022_2025": block(test_rows, kinds),
        "first_half_weeks_le_7": block([r for r in pooled if r["week"] <= 7], kinds),
        "second_half_weeks_ge_8": block([r for r in pooled if r["week"] >= 8], kinds),
        "test_second_half": block([r for r in test_rows if r["week"] >= 8], kinds),
        "by_season": {s: block([r for r in rows if r["season"] == s], kinds) for s in targets},
        "ci95_brier": {
            "selected_minus_standard_pooled": clustered_bootstrap(pooled, selected, "standard"),
            "selected_minus_standard_test": clustered_bootstrap(test_rows, selected, "standard"),
            "selected_minus_standard_test_second_half": clustered_bootstrap([r for r in test_rows if r["week"] >= 8], selected, "standard"),
            "standard_minus_incumbent_pooled": clustered_bootstrap(pooled, "standard", "incumbent"),
            "selected_minus_incumbent_pooled": clustered_bootstrap(pooled, selected, "incumbent"),
        },
        "calibration": {k: {"slope": calibration_slope([r[k] for r in pooled], [r["y"] for r in pooled]),
                            "bins": calibration_bins([r[k] for r in pooled], [r["y"] for r in pooled])} for k in ["standard", selected, "incumbent"]},
        "season_records": record_accuracy(snapshots, kinds, scales),
        "authentic_2026": authentic_2026(records, ["standard", selected]),
        "scales": {k: {str(s): v for s, v in sc.items()} for k, sc in scales.items()},
        # For live 2026 projections: logistic scale fitted on every evaluated season (2016-2025, not 2020).
        "final_scales": {k: dp.fit_scale([r["models"][k][2] for r in hist if r["season"] != 2020],
                                         [r["y"] for r in hist if r["season"] != 2020]) for k in kinds},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(round_tree(result), indent=1, sort_keys=True) + "\n")
    p, t = result["pooled_2017_2025"], result["test_seasons_2022_2025"]
    for name, b in (("pooled", p), ("test", t), ("2nd half", result["second_half_weeks_ge_8"])):
        print(name, {k: round(b[k]["brier"], 4) for k in ["incumbent_replay", "standard", selected]})
    print("selected", selected, "CI", result["ci95_brier"])
    print("records", {k: round(v["mae_wins"], 3) for k, v in result["season_records"].items()})


if __name__ == "__main__":
    main()
