"""Publish "Why this prediction?" explanation data for every upcoming FBS matchup (no new model).

  python -m cfb_analytics.explain_publish     # writes web/public/prediction-explanations.json

Every number is an exact decomposition of an existing published forecast:

* Official (workbook engine, `ratings.calculate_ratings`): a team's rating is
  (sum of game values + 5 x preseason prior) / (games + 5), where a game value is the opponent's rating plus the
  home-adjusted margin. The engine is re-run from the same frozen roster and CFBD snapshot as the season report, and
  publishing stops unless every rating and margin equals the report.
* Standard and Momentum (`dual_projection`): net rating = (weighted sum of opponent-adjusted game values + 3 x prior)
  / (weights + 3); projected points = league average + offense + opponent defense + home field. Re-run exactly as
  `dual_publish` does; the tests check the margins equal `dual_publish.build`.

Schedule strength, quality wins and records are context only: they are already inside the ratings, so they are never
added as separate points. Quarterback changes, injuries and weather are not inputs to any model and are listed as
unavailable rather than inferred.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from . import dual_projection as dp
from . import dual_publish as pub
from .parity import load_baseline
from .ratings import Game, Team, calculate_ratings
from .model import ModelSettings, adjusted_home_margin

OUT = Path("web/public/prediction-explanations.json")
ALIASES = {"Miami": "Miami (FL)", "App State": "Appalachian State", "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}
UNAVAILABLE = [
    "Quarterback changes and starters: no verified pregame source, so no model includes them",
    "Injuries, suspensions and opt-outs",
    "Weather, travel and rest days",
    "Betting-market information (shown separately in Market analysis)",
]
TOL = 1e-6


def official_components(report, snapshot, settings=ModelSettings()):
    """Re-run the workbook engine; return per-team rating parts. Raises if it does not reproduce the report."""
    roster, _ = load_baseline()
    teams = [Team(t["name"], t["conference"], t["prior"]) for t in roster]
    games = [Game(ALIASES.get(g["home"], g["home"]), ALIASES.get(g["away"], g["away"]), g["home_score"], g["away_score"], g["week"])
             for g in snapshot["games"] if g["completed"]]
    ratings = calculate_ratings(teams, games, settings)
    published = {r["team"]: r for r in report["rankings"]}
    for name, r in published.items():
        if abs(ratings[name].adaptive_rating - r["rating"]) > TOL:
            raise ValueError(f"Official rating for {name} does not reproduce the season report")
    # Same pass selection as calculate_ratings; game values use the pass before it.
    completed = len(games)
    chosen = 5 if completed < 200 else 6 if completed < 400 else 7 if completed < 650 else 8
    prev = {n: r.passes[chosen - 1] for n, r in ratings.items()}
    out = {}
    ridge = settings.ridge_strength
    for name, r in ratings.items():
        values = []
        for g in games:
            if name not in (g.home, g.away):
                continue
            home = g.home == name
            opp = g.away if home else g.home
            m = adjusted_home_margin(g.home_score, g.away_score, settings)
            values.append(prev.get(opp, settings.fcs_opponent_rating) + (m if home else -m))
        n = len(values)
        games_part = sum(values) / (n + ridge)
        prior_part = r.adaptive_rating - games_part
        out[name] = {"rating": r.adaptive_rating, "games": n, "games_part": games_part, "prior_part": prior_part,
                     "games_average": sum(values) / n if n else None, "schedule_strength": r.strength_of_schedule,
                     "quality_wins": r.quality_wins, "bad_losses": r.bad_losses}
    # Check the decomposition: the prior part must equal ridge x (prior + conference shift) / (games + ridge).
    conf = {t.name: t.conference for t in teams}
    first = {t.name: t.prior for t in teams}
    for name, c in out.items():
        members = [t for t in conf if conf[t] == conf[name]]
        shift = sum(prev[t] for t in members) / len(members) - sum(first[t] for t in members) / len(members)
        expected = ridge * (first[name] * settings.prior_year_weight + settings.conference_shrink * shift) / (c["games"] + ridge)
        if abs(expected - c["prior_part"]) > 1e-6:
            raise ValueError(f"Official decomposition does not close for {name}")
        c["effective_prior"] = first[name] * settings.prior_year_weight + settings.conference_shrink * shift
    return out


def dual_components(snapshot, evaluation, membership):
    """Re-run Standard and Momentum exactly as dual_publish does; return fit, per-model ratings and game values."""
    season = snapshot["season"]
    fbs = set(membership[str(season)])
    dp.REGRESS = evaluation["prior_tuning"]["chosen"]["regress"]
    dp.PRIOR_GAMES = evaluation["prior_tuning"]["chosen"]["prior_games"]
    momentum = evaluation["selected_momentum"]
    kinds = {"standard": None, "momentum": dp.WEIGHTINGS[momentum][1]}
    scales = {"standard": evaluation["final_scales"]["standard"], "momentum": evaluation["final_scales"][momentum]}
    priors = pub.chain_priors(season)
    rows = pub.current_rows(snapshot["games"], fbs)
    fit = dp.stage1(rows, {t: priors.get(t, dp.NEW_TEAM) for t in fbs})
    values = dp.game_values(rows, fit)
    ratings = {k: dp.model_ratings(values, fit, kind) for k, kind in kinds.items()}
    return {"fbs": fbs, "kinds": kinds, "scales": scales, "fit": fit, "values": values, "ratings": ratings, "rows": rows}


def dual_team(d, team):
    """Per-model net rating split into this season's games and the preseason prior (exact)."""
    games = d["values"].get(team, [])
    prior = d["fit"]["prior"][team]
    out = {}
    for k, kind in d["kinds"].items():
        w = dp.weights(len(games), kind)
        denom = sum(w) + dp.PRIOR_GAMES
        o, de = d["ratings"][k][team]
        out[k] = {"net": o - de, "offense": o, "defense": de,
                  "games_part": sum(wi * (g[2] - g[3]) for wi, g in zip(w, games)) / denom,
                  "prior_part": dp.PRIOR_GAMES * (prior[0] - prior[1]) / denom}
    return out


def weakest_game(d, team):
    """The team's lowest opponent-adjusted game (Standard), with opponent and score, for data-driven notes."""
    by_id = {r["game_id"]: r for r in d["rows"] if r["team"] == team}
    games = d["values"].get(team, [])
    if not games:
        return None
    date, gid, a, b = min(games, key=lambda g: g[2] - g[3])
    r = by_id[gid]
    return {"opponent": r["opp"], "opponent_fbs": r["opp_fbs"], "points_for": r["pf"], "points_against": r["pa"],
            "net_value": round(a - b, 2), "season_average": round(sum(g[2] - g[3] for g in games) / len(games), 2)}


def build(report, snapshot, evaluation, membership, settings=ModelSettings()):
    official = official_components(report, snapshot, settings)
    d = dual_components(snapshot, evaluation, membership)
    to_report = pub.report_names(d["fbs"])
    to_model = {v: k for k, v in to_report.items()}
    fit = d["fit"]
    fbs_model = {k: v for k, v in d["fit"]["off"].items() if k in d["fbs"]}
    rank = lambda values, reverse: {t: i + 1 for i, t in enumerate(sorted(values, key=lambda t: values[t], reverse=reverse))}
    net_rank = {k: rank({t: d["ratings"][k][t][0] - d["ratings"][k][t][1] for t in d["fbs"]}, True) for k in d["kinds"]}
    off_rank = rank({t: d["ratings"]["standard"][t][0] for t in d["fbs"]}, True)
    def_rank = rank({t: d["ratings"]["standard"][t][1] for t in d["fbs"]}, False)
    ranked = {r["team"]: r for r in report["rankings"]}
    sos = {t: official[t]["schedule_strength"] for t in ranked}
    sos_rank = rank(sos, True)
    upcoming = {g["game_id"] for g in report["schedule"] if not g["completed"]}
    teams, games = {}, []
    for p in report["predictions"]:
        if p["game_id"] not in upcoming or p["home"] not in ranked or p["away"] not in ranked:
            continue
        hm, am = to_model.get(p["home"], p["home"]), to_model.get(p["away"], p["away"])
        if hm not in fbs_model or am not in fbs_model:
            continue
        neutral = p["neutral_site"]
        o_home = 0.0 if neutral else settings.home_field_advantage
        oh, oa = official[p["home"]], official[p["away"]]
        parts = {"official": {"season_games": oh["games_part"] - oa["games_part"], "preseason_prior": oh["prior_part"] - oa["prior_part"],
                              "home_field": o_home, "home_margin": p["home_margin"]}}
        if abs(sum(v for k, v in parts["official"].items() if k != "home_margin") - p["home_margin"]) > TOL:
            raise ValueError(f"Official decomposition does not equal the published margin for game {p['game_id']}")
        th, ta = dual_team(d, hm), dual_team(d, am)
        for k in d["kinds"]:
            hp, ap, margin = dp.project(hm, am, neutral, d["ratings"][k], fit)
            part = {"season_games": th[k]["games_part"] - ta[k]["games_part"], "preseason_prior": th[k]["prior_part"] - ta[k]["prior_part"],
                    "home_field": 0.0 if neutral else 2 * fit["home"], "home_margin": margin,
                    "home_points": hp, "away_points": ap,
                    # Points above the league average each offense is projected to score against this defense.
                    "home_offense_vs_away_defense": th[k]["offense"] + ta[k]["defense"],
                    "away_offense_vs_home_defense": ta[k]["offense"] + th[k]["defense"],
                    "home_win_probability": dp.probability(margin, d["scales"][k])}
            if abs(part["season_games"] + part["preseason_prior"] + part["home_field"] - margin) > TOL:
                raise ValueError(f"{k} decomposition does not equal its margin for game {p['game_id']}")
            parts[k] = part
        for name, model_name, dual in ((p["home"], hm, th), (p["away"], am, ta)):
            if name in teams:
                continue
            o, r = official[name], ranked[name]
            teams[name] = {
                "wins": r["wins"], "losses": r["losses"], "official_rank": r["rank"], "official_rating": round(o["rating"], 3),
                "official_games_average": round(o["games_average"], 2) if o["games_average"] is not None else None,
                "official_effective_prior": round(o["effective_prior"], 2),
                "schedule_strength": round(o["schedule_strength"], 2), "schedule_rank": sos_rank[name], "schedule_teams": len(sos_rank),
                "quality_wins": o["quality_wins"], "bad_losses": o["bad_losses"],
                "standard_net_rank": net_rank["standard"][model_name], "momentum_net_rank": net_rank["momentum"][model_name],
                "offense_rank": off_rank[model_name], "defense_rank": def_rank[model_name], "fbs_teams": len(d["fbs"]),
                "recent_form": pub.form(d["values"], model_name), "standard_net": round(dual["standard"]["net"], 2),
                "season_game_average": round(sum(g[2] - g[3] for g in d["values"][model_name]) / len(d["values"][model_name]), 2) if d["values"].get(model_name) else None,
                "momentum_net": round(dual["momentum"]["net"], 2), "weakest_game": weakest_game(d, model_name)}
        games.append({"game_id": p["game_id"], "week": p["week"], "home": p["home"], "away": p["away"], "neutral_site": neutral,
                      **{k: {f: round(v, 3) for f, v in part.items()} for k, part in parts.items()}})
    return {"schema_version": 1, "season": report["season"], "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "data_retrieved_at": snapshot.get("retrieved_at"), "report_retrieved_at": report.get("retrieved_at"),
            "official_home_field": settings.home_field_advantage, "official_prior_games": settings.ridge_strength,
            "dual_prior_games": dp.PRIOR_GAMES, "dual_home_field": round(2 * fit["home"], 3), "league_average_points": round(fit["mean"], 2),
            "unavailable": UNAVAILABLE, "games": games, "teams": teams}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    report = json.loads(Path("data/season-2026-report.json").read_text())
    snapshot = json.loads(Path("data/cfbd-2026-games.json").read_text())
    if report.get("retrieved_at") != snapshot.get("retrieved_at"):
        raise SystemExit("season report and CFBD snapshot differ; rebuild the report first")
    payload = build(report, snapshot, json.loads(pub.EVAL.read_text()), json.loads(Path("research/v8/fbs-membership.json").read_text()))
    args.out.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")
    print(f"{args.out}: {len(payload['games'])} explained games, {len(payload['teams'])} teams, {args.out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
