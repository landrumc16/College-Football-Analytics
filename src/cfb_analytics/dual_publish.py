"""Publish current-season Standard and Momentum projections for the web app (preview; production forecasts unchanged).

  python -m cfb_analytics.dual_publish     # writes web/public/dual-projections.json

Completed 2026 scores come from data/cfbd-2026-games.json (the routinely refreshed CFBD snapshot); FBS membership
from research/v8/fbs-membership.json; preseason priors from chaining the same Standard fit over 2016-2025 (V8 data).
Conference, CFP and national-title odds reuse the incumbent simulate_cfp rules unchanged, fed each model's own
ratings, home edge and probability scale.
"""
import argparse
import gzip
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from . import dual_projection as dp
from . import v8_stats as st
from .cfp import simulate_cfp
from .v6_scenarios import scenario_input

OUT = Path("web/public/dual-projections.json")
EVAL = Path("research/dual/evaluation.json")
MODELS = {"standard": "standard"}  # momentum key is filled from the evaluation's selected decay


def chain_priors(until):
    """Preseason priors for season `until`: chain the Standard fit over every earlier V8 season."""
    priors = {}
    for season in range(2016, until):
        rows = st.load_rows(season)
        full = {t: priors.get(t, dp.NEW_TEAM) for t in {r["team"] for r in rows if r["team_fbs"]}}
        fit = dp.stage1(rows, full)
        priors = dp.next_priors(dp.model_ratings(dp.game_values(rows, fit), fit, None))
    return priors


def current_rows(games, fbs):
    """Team-game rows (both sides) for completed games involving an FBS team, from the CFBD snapshot."""
    rows = []
    for g in games:
        if not g["completed"] or g["home_score"] is None or not (g["home"] in fbs or g["away"] in fbs):
            continue
        for team, opp, pf, pa, side in ((g["home"], g["away"], g["home_score"], g["away_score"], "home"),
                                        (g["away"], g["home"], g["away_score"], g["home_score"], "away")):
            rows.append({"game_id": str(g["game_id"]), "date": g["start_date"], "team": team, "opp": opp, "pf": pf, "pa": pa,
                         "site": "neutral" if g["neutral_site"] else side, "team_fbs": team in fbs, "opp_fbs": opp in fbs})
    return rows


def form(values, team, n=3):
    """Average opponent-adjusted net value over the team's last n games, for the explanation (offense minus defense)."""
    games = values.get(team, [])[-n:]
    return round(sum(g[2] - g[3] for g in games) / len(games), 2) if games else None


def report_names(fbs):
    """Map CFBD school names (used by the models) to the report's canonical names, one-to-one.

    The season report and the CFP simulation inputs use canonical names (for example "Miami (FL)"), while the CFBD
    snapshot uses "Miami". Every lookup between the two must go through this map so that no team is silently dropped.
    """
    from scripts.reconcile_v5_historical_sources import canonical
    names = {t: canonical(t) for t in fbs}
    if len(set(names.values())) != len(names):
        raise ValueError("FBS school names do not map one-to-one to report names")
    return names


def tiebreak_swaps(conference, standard, momentum, contenders):
    """Same-conference contender pairs whose rating order differs between the two models.

    The shared CFP simulation picks conference-title-game teams by conference wins and breaks ties by model rating, so
    when two contenders swap order between models every tied scenario changes hands. This is a legitimate consequence
    of the shared rules (both models use them identically) but it can move conference and CFP odds far more than the
    small rating change suggests, so the page names the swap. Returns team -> sorted list of
    {"rival", "standard_gap", "momentum_gap"} with gaps from the team's point of view.
    """
    out = {}
    names = sorted(t for t in contenders if t in standard and t in momentum)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if conference.get(a) is None or conference.get(a) != conference.get(b):
                continue
            ds, dm = standard[a] - standard[b], momentum[a] - momentum[b]
            if ds * dm < 0:
                out.setdefault(a, []).append({"rival": b, "standard_gap": round(ds, 2), "momentum_gap": round(dm, 2)})
                out.setdefault(b, []).append({"rival": a, "standard_gap": round(-ds, 2), "momentum_gap": round(-dm, 2)})
    return {t: sorted(v, key=lambda x: x["rival"]) for t, v in out.items()}


def build(report, snapshot, evaluation, membership):
    season = snapshot["season"]
    fbs = set(membership[str(season)])
    to_report = report_names(fbs)
    to_model = {v: k for k, v in to_report.items()}
    dp.REGRESS = evaluation["prior_tuning"]["chosen"]["regress"]
    dp.PRIOR_GAMES = evaluation["prior_tuning"]["chosen"]["prior_games"]
    momentum = evaluation["selected_momentum"]
    kinds = {"standard": None, "momentum": dp.WEIGHTINGS[momentum][1]}
    scales = {"standard": evaluation["final_scales"]["standard"], "momentum": evaluation["final_scales"][momentum]}
    priors = chain_priors(season)
    rows = current_rows(snapshot["games"], fbs)
    fit = dp.stage1(rows, {t: priors.get(t, dp.NEW_TEAM) for t in fbs})
    values = dp.game_values(rows, fit)
    ratings = {k: dp.model_ratings(values, fit, kind) for k, kind in kinds.items()}
    official = {p["game_id"]: p for p in report["predictions"]}
    upcoming = sorted((g for g in snapshot["games"] if not g["completed"] and (g["home"] in fbs or g["away"] in fbs)),
                      key=lambda g: (g["start_date"] or "", g["game_id"]))
    games = []
    for g in upcoming:
        entry = {"game_id": g["game_id"], "week": g["week"], "start_date": g["start_date"], "home": g["home"], "away": g["away"],
                 "neutral_site": g["neutral_site"], "home_fbs": g["home"] in fbs, "away_fbs": g["away"] in fbs,
                 "home_form": form(values, g["home"]), "away_form": form(values, g["away"])}
        for k in kinds:
            hp, ap, m = dp.project(g["home"], g["away"], g["neutral_site"], ratings[k], fit)
            entry[k] = {"home_points": round(hp, 1), "away_points": round(ap, 1), "home_margin": round(m, 2),
                        "home_win_probability": round(dp.probability(m, scales[k]), 4)}
        o = official.get(g["game_id"])
        entry["official"] = ({"home_win_probability": round(o["home_win_probability"], 4), "home_margin": round(o["home_margin"], 2)}
                             if o and o["home"] == to_report.get(g["home"], g["home"]) else None)
        games.append(entry)
    # Season records: actual wins/losses plus each model's exact distribution over remaining games.
    record = {t: [0, 0] for t in fbs}
    for g in snapshot["games"]:
        if g["completed"] and g["home_score"] is not None and g["home_score"] != g["away_score"]:
            w, l = (g["home"], g["away"]) if g["home_score"] > g["away_score"] else (g["away"], g["home"])
            if w in record: record[w][0] += 1
            if l in record: record[l][1] += 1
    teams = {}
    for t in sorted(fbs):
        mine = [x for x in games if t in (x["home"], x["away"])]
        entry = {"wins": record[t][0], "losses": record[t][1], "remaining": len(mine)}
        for k in kinds:
            ps = [x[k]["home_win_probability"] if x["home"] == t else 1 - x[k]["home_win_probability"] for x in mine]
            dist = dp.win_distribution(ps)
            exp = record[t][0] + sum(ps)
            entry[k] = {"expected_wins": round(exp, 2), "expected_losses": round(record[t][1] + len(ps) - sum(ps), 2),
                        "win_distribution": [round(q, 4) for q in dist],
                        "rating": round(ratings[k][t][0] - ratings[k][t][1], 2) if t in ratings[k] else None,
                        "offense": round(ratings[k][t][0], 2) if t in ratings[k] else None,
                        "defense": round(ratings[k][t][1], 2) if t in ratings[k] else None}
        teams[t] = entry
    # Conference, CFP and title odds: unchanged incumbent simulation rules with each model's ratings.
    base = scenario_input(report, snapshot)
    official_cfp = {t["team"]: t for t in report.get("cfp", {}).get("teams", [])}
    model_name = lambda name: to_model.get(name, name)
    missing = sorted(t for t in base["teams"] if model_name(t) not in teams or model_name(t) not in ratings["standard"])
    if missing:
        raise ValueError(f"CFP simulation teams without a model rating: {missing}")
    sim_games = [{"home": model_name(g["home"]), "away": model_name(g["away"]), "neutral_site": g["neutral_site"]} for g in base["games"]]
    published = {(x["home"], x["away"]) for x in games}
    if any((g["home"], g["away"]) not in published for g in sim_games if g["home"] in fbs or g["away"] in fbs):
        raise ValueError("CFP simulation schedule differs from the published game projections")
    for k in kinds:
        sim_teams = {model_name(t): {**v, "rating": ratings[k][model_name(t)][0] - ratings[k][model_name(t)][1]} for t, v in base["teams"].items()}
        result = simulate_cfp(sim_teams, sim_games, simulations=10000, seed=2026, scale=scales[k] * math.log(10),
                              home_edge=2 * fit["home"], fcs_rating=ratings[k][dp.FCS][0] - ratings[k][dp.FCS][1])
        for row in result["teams"]:
            name = row["team"]
            if name in teams:
                teams[name][k].update({"conference_title": row.get("conference_title"), "cfp_field": row.get("cfp_field"),
                                       "national_title": row.get("national_title")})
    # Contenders: a realistic chance at the conference title game in either model.
    conference = {model_name(t): v["conference"] for t, v in base["teams"].items()}
    rating = {k: {t: ratings[k][t][0] - ratings[k][t][1] for t in teams if t in ratings[k]} for k in kinds}
    contenders = {t for t, e in teams.items() if max(e["standard"]["conference_title"] or 0, e["momentum"]["conference_title"] or 0) >= 0.02}
    swaps = tiebreak_swaps(conference, rating["standard"], rating["momentum"], contenders)
    for t, entry in teams.items():
        entry["tiebreak_swaps"] = swaps.get(t, [])
        o = official_cfp.get(to_report[t])
        entry["official"] = {"cfp_field": o.get("cfp_field"), "conference_title": o.get("conference_title")} if o else None
    pooled, test = evaluation["pooled_2017_2025"], evaluation["test_seasons_2022_2025"]
    summary = lambda b: {k: {m: round(b[key][m], 4) for m in ("brier", "log_loss", "winner_accuracy", "margin_mae")}
                         for k, key in (("standard", "standard"), ("momentum", momentum), ("incumbent_replay", "incumbent_replay"))}
    return {"schema_version": 1, "season": season, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "data_retrieved_at": snapshot.get("retrieved_at"), "status": "preview: official forecasts still come from the existing model",
            "models": {"standard": {"label": "Standard", "weighting": "every completed game counts equally"},
                       "momentum": {"label": "Momentum", "weighting": f"stair-step: newest game counts most ({dp.WEIGHTINGS[momentum][0]})",
                                    "decay": momentum}},
            "method": {"opponents": "one shared opponent-strength fit of points scored and allowed (counted once); FCS opponents pooled",
                       "games": f"each game's opponent-adjusted value is capped at +/-{dp.CLIP:g} points",
                       "priors": f"preseason prior = {dp.REGRESS:g} x last season's final rating, worth {dp.PRIOR_GAMES:g} games",
                       "probability": "logistic in projected margin, scale fitted on 2016-2025 (not 2020)",
                       "records": "actual record plus the exact win distribution of each model's own game probabilities",
                       "playoffs": "conference, CFP and title odds use the existing simulation rules (10,000 seasons) with each model's ratings",
                       "tiebreaks": "the simulation breaks tied conference records by model rating, so two contenders that swap order between "
                                    "the models can see their conference and CFP odds move much more than their projected records"},
            "home_field_points": round(2 * fit["home"], 2), "scales": {k: round(v, 3) for k, v in scales.items()},
            "validation": {"pooled_2017_2025": summary(pooled), "test_2022_2025": summary(test),
                           "second_half": summary(evaluation["second_half_weeks_ge_8"]),
                           "games": pooled["games"], "test_games": test["games"],
                           "authentic_2026": {k: round(evaluation["authentic_2026"][key]["brier"], 4) for k, key in
                                              (("standard", "standard"), ("momentum", momentum), ("published_incumbent", "published_incumbent"))},
                           "authentic_2026_games": evaluation["authentic_2026"]["games"],
                           "season_records_mae_wins": {k: round(evaluation["season_records"][key]["mae_wins"], 3) for k, key in
                                                       (("standard", "standard"), ("momentum", momentum), ("incumbent_replay", "incumbent"))}},
            "games": games, "teams": teams}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    report = json.loads(Path("data/season-2026-report.json").read_text())
    snapshot = json.loads(Path("data/cfbd-2026-games.json").read_text())
    payload = build(report, snapshot, json.loads(EVAL.read_text()), json.loads(Path("research/v8/fbs-membership.json").read_text()))
    args.out.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"{args.out}: {len(payload['games'])} upcoming games, {len(payload['teams'])} teams, {args.out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
