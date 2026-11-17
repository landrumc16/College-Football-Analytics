"""V7 Milestone 6: honest historical validation (frozen, reproducible, aggregates only).

1. Archive integrity: every published per-game line is re-joined to the verified results sources
   (research/archive/verified/espn-games.json.gz for 2016-2025, data/cfbd-2026-games.json for 2026)
   and its ATS / over-under letters are recomputed with plain arithmetic.
2. National descriptive market checks: favourite/home cover and over rates with Wilson intervals.
3. Model vs market accuracy on identical games, using only forecasts recorded before kickoff
   (the M3 authentic comparison rows), with a 50/50 reference, paired bootstrap intervals,
   calibration and a disagreement-information test. No retrospective replays, no model totals,
   no profitability claims.

Output: research/v7/historical-validation.json. `--check` requires byte-identical regeneration.
"""
import argparse
import gzip
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path

from .forecast_ledger import ALIASES
from .v7_market_metrics import (COMPARISON_DIR, LEDGER, LINES_DIR, MODEL_TOTAL, VERIFIED, assert_metrics_safe,
                                implied_probability, wilson)

ARCHIVE = Path("research/archive/verified/espn-games.json.gz")
CURRENT = Path("data/cfbd-2026-games.json")
OUTPUT = Path("research/v7/historical-validation.json")
BOOTSTRAP = 10000
SEED = 20261116
EPS = 1e-15


class ValidationFailed(RuntimeError):
    pass


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_dir(directory):
    h = hashlib.sha256()
    for f in sorted(Path(directory).glob("*.json")):
        h.update(f.name.encode() + b"\0" + f.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------- 1. archive integrity
def results_index(archive=ARCHIVE, current=CURRENT):
    out = {}
    for season, games in json.loads(gzip.decompress(Path(archive).read_bytes())).items():
        for g in games:
            out[str(g["game_id"])] = (g["home"], g["away"], g["home_score"], g["away_score"], bool(g.get("neutral_site")))
    for g in json.loads(Path(current).read_text())["games"]:
        if g.get("completed") and g.get("home_score") is not None:
            home, away = ALIASES.get(g["home"], g["home"]), ALIASES.get(g["away"], g["away"])
            out[str(g["game_id"])] = (home, away, g["home_score"], g["away_score"], bool(g.get("neutral_site")))
    return out


def integrity(lines, index):
    checked = mismatched_scores = mismatched_letters = missing = 0
    problems = []
    for team, games in sorted(lines.items()):
        for g in games:
            r = index.get(str(g["game_id"]))
            if r is None:
                missing += 1
                problems.append(f"{team} {g['game_id']}: not in verified sources")
                continue
            home, away, hs, as_, neutral = r
            if team == home:
                expect = (away, hs, as_, "neutral" if neutral else "home")
            elif team == away:
                expect = (home, as_, hs, "neutral" if neutral else "away")
            else:
                mismatched_scores += 1
                problems.append(f"{team} {g['game_id']}: team not in game")
                continue
            if (g["opponent"], g["team_score"], g["opponent_score"], g["venue"]) != expect:
                mismatched_scores += 1
                problems.append(f"{team} {g['game_id']}: identity/score/venue differs")
            checked += 1
            margin = g["team_score"] - g["opponent_score"]
            if g["spread"] is not None:
                c = margin + g["spread"]
                if g["ats"] != ("W" if c > 0 else "L" if c < 0 else "P"):
                    mismatched_letters += 1
                    problems.append(f"{team} {g['game_id']}: ATS letter")
            if g["total"] is not None:
                d = g["team_score"] + g["opponent_score"] - g["total"]
                if g["ou"] != ("O" if d > 0 else "U" if d < 0 else "P"):
                    mismatched_letters += 1
                    problems.append(f"{team} {g['game_id']}: O/U letter")
    return {"team_game_rows_checked": checked, "missing_from_verified_sources": missing,
            "identity_score_or_venue_mismatches": mismatched_scores, "ats_or_ou_letter_mismatches": mismatched_letters,
            "sources": ["research/archive/verified/espn-games.json.gz (2016-2025)", "data/cfbd-2026-games.json (2026 completed)"],
            "status": "passed" if not problems else "failed"}, problems


# ---------------------------------------------------------------- 2. national descriptive checks
def unique_games(lines):
    """Each game once: home side, else alphabetically first team (neutral), else the only FBS team."""
    chosen = {}
    for team, games in sorted(lines.items()):
        for g in games:
            if g["game_id"] not in chosen or g["venue"] == "home":
                chosen[g["game_id"]] = g
    return list(chosen.values())


def rate(successes, failures):
    n = successes + failures
    return {"n": n, "rate": round(successes / n, 4) if n else None, "ci95": wilson(successes, n)}


def national(lines):
    games = [g for g in unique_games(lines) if g["team_score"] is not None]
    spread = [g for g in games if g["spread_status"] == "ok" and g["spread"] != 0]
    total = [g for g in games if g["total_status"] == "ok"]
    def fav_cover(g):     # favourite = side with negative spread from this row's perspective
        c = g["team_score"] - g["opponent_score"] + g["spread"]
        return 0 if c == 0 else (1 if (c > 0) == (g["spread"] < 0) else -1)
    fav = [fav_cover(g) for g in spread]
    home = [g for g in games if g["spread_status"] == "ok" and g["venue"] == "home"]
    home_c = [g["team_score"] - g["opponent_score"] + g["spread"] for g in home]
    ou = [g["team_score"] + g["opponent_score"] - g["total"] for g in total]
    by_season = {}
    for g, f in zip(spread, fav):
        s = by_season.setdefault(str(g["season"]), [0, 0])
        if f == 1:
            s[0] += 1
        elif f == -1:
            s[1] += 1
    return {
        "games": len(games),
        "favorite_cover": {**rate(fav.count(1), fav.count(-1)), "pushes": fav.count(0)},
        "favorite_cover_by_season": {s: rate(*v) for s, v in sorted(by_season.items())},
        "home_cover_non_neutral": {**rate(sum(c > 0 for c in home_c), sum(c < 0 for c in home_c)), "pushes": sum(c == 0 for c in home_c)},
        "over": {**rate(sum(d > 0 for d in ou), sum(d < 0 for d in ou)), "pushes": sum(d == 0 for d in ou)},
        "interpretation": "Rates near 50% are what an efficient closing market implies. These are descriptive checks of the "
                          "archive, not betting strategies; the published rates exclude pushes and ignore bookmaker margin.",
    }


# ---------------------------------------------------------------- 3. model vs market on identical games
def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = min(max(p, EPS), 1 - EPS)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def paired_bootstrap(diffs, seed=SEED, n=BOOTSTRAP):
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(statistics.fmean(diffs[rng.randrange(k)] for _ in range(k)) for _ in range(n))
    return [round(means[int(0.025 * n)], 4), round(means[int(0.975 * n) - 1], 4)]


def scores(rows, key):
    ps = [r[key] for r in rows]
    ys = [r["y"] for r in rows]
    return {"brier": round(statistics.fmean(brier(p, y) for p, y in zip(ps, ys)), 4),
            "log_loss": round(statistics.fmean(logloss(p, y) for p, y in zip(ps, ys)), 4),
            "winner_accuracy": round(statistics.fmean((p > 0.5) == (y == 1) if p != 0.5 else 0.5 for p, y in zip(ps, ys)), 4)}


def calibration(rows, key, edges=(0, 0.2, 0.4, 0.6, 0.8, 1.0001)):
    out = []
    for lo, hi in zip(edges, edges[1:]):
        sub = [r for r in rows if lo <= r[key] < hi]
        wins = sum(r["y"] for r in sub)
        out.append({"lower": lo, "upper": min(hi, 1.0), "games": len(sub),
                    "mean_predicted": round(statistics.fmean(r[key] for r in sub), 3) if sub else None,
                    "observed_home_win_rate": round(wins / len(sub), 3) if sub else None, "ci95": wilson(wins, len(sub))})
    return out


def evaluate(rows, label):
    if len(rows) < 10:
        return {"population": label, "games": len(rows), "na_reason": "fewer than 10 completed authentic games"}
    for r in rows:
        r["blend"] = (r["model"] + r["market"]) / 2
    d_brier = [brier(r["model"], r["y"]) - brier(r["market"], r["y"]) for r in rows]
    d_log = [logloss(r["model"], r["y"]) - logloss(r["market"], r["y"]) for r in rows]
    d_blend = [brier(r["blend"], r["y"]) - brier(r["market"], r["y"]) for r in rows]
    d_mae = [abs(r["model_margin"] - r["actual_margin"]) - abs(r["market_margin"] - r["actual_margin"]) for r in rows]
    disagree = [r for r in rows if (r["model"] - 0.5) * (r["market"] - 0.5) < 0]
    model_fav_won = sum(1 for r in disagree if (r["model"] > 0.5) == (r["y"] == 1))
    above = [r["y"] - r["market"] for r in rows if r["model"] > r["market"]]
    below = [r["y"] - r["market"] for r in rows if r["model"] < r["market"]]
    # Disagreement information: does the outcome residual against the market lean the model's way?
    signed = [(r["y"] - r["market"]) * (1 if r["model"] > r["market"] else -1) for r in rows if r["model"] != r["market"]]
    ci = lambda xs: paired_bootstrap(xs)
    out = {
        "population": label, "games": len(rows),
        "model": scores(rows, "model"), "market_spread_implied": scores(rows, "market"),
        "neutral_50_50": scores([{**r, "half": 0.5} for r in rows], "half"),
        "model_market_average": scores(rows, "blend"),
        "paired_differences_model_minus_market": {
            "brier": {"mean": round(statistics.fmean(d_brier), 4), "ci95": ci(d_brier)},
            "log_loss": {"mean": round(statistics.fmean(d_log), 4), "ci95": ci(d_log)},
            "margin_absolute_error_points": {"mean": round(statistics.fmean(d_mae), 2), "ci95": ci(d_mae)},
        },
        "margin_mae_points": {"model": round(statistics.fmean(abs(r["model_margin"] - r["actual_margin"]) for r in rows), 2),
                              "market": round(statistics.fmean(abs(r["market_margin"] - r["actual_margin"]) for r in rows), 2)},
        "average_minus_market_brier": {"mean": round(statistics.fmean(d_blend), 4), "ci95": ci(d_blend)},
        "favorite_disagreements": {"games": len(disagree), "model_favorite_won": model_fav_won,
                                   "model_favorite_win_rate": round(model_fav_won / len(disagree), 3) if disagree else None,
                                   "ci95": wilson(model_fav_won, len(disagree))},
        "disagreement_information": {
            "games_model_above_market": len(above), "mean_outcome_minus_market_when_model_above": round(statistics.fmean(above), 3) if above else None,
            "games_model_below_market": len(below), "mean_outcome_minus_market_when_model_below": round(statistics.fmean(below), 3) if below else None,
            "signed_residual_toward_model": ({"mean": round(statistics.fmean(signed), 4), "ci95": ci(signed)} if signed
                                             else {"mean": None, "ci95": None, "na_reason": "model and market never differ"}),
            "reading": "Positive would mean outcomes moved, on average, in the direction the model disagreed with the market.",
        },
        "calibration": {"model": calibration(rows, "model"), "market_spread_implied": calibration(rows, "market")},
    }
    out["conclusion"] = conclusion(out)
    return out


def conclusion(e):
    d = e["paired_differences_model_minus_market"]["brier"]
    s = e["disagreement_information"]["signed_residual_toward_model"]
    if d["ci95"][0] > 0:
        accuracy = "The closing-spread market was more accurate than the model on these games (Brier interval excludes zero)."
    elif d["ci95"][1] < 0:
        accuracy = "The model was more accurate than the closing-spread market on these games (Brier interval excludes zero)."
    else:
        accuracy = "Inconclusive: the Brier difference between model and market is not distinguishable from zero on this sample."
    info = ("No model-market disagreement to evaluate." if s["ci95"] is None else
            "No evidence that model-market disagreement carried information beyond the market (interval includes zero)."
            if s["ci95"][0] <= 0 <= s["ci95"][1] else
            "Disagreement residuals lean toward the model; small sample, not a strategy." if s["ci95"][0] > 0 else
            "Disagreement residuals lean against the model.")
    return f"{accuracy} {info}"


def comparison_population(comparison_dir=COMPARISON_DIR):
    rows = {}
    for f in sorted(Path(comparison_dir).glob("*.json")):
        for g in json.loads(f.read_text())["games"]:
            if g["home_score"] is None or g["home_score"] == g["away_score"]:
                continue
            if g["forecast_kind"] != "authentic_pregame":
                raise ValidationFailed("non-authentic forecast in comparison input")
            rows[g["game_id"]] = {"y": int(g["home_score"] > g["away_score"]), "model": g["model_home_win_probability"],
                                  "market": implied_probability(g["home_spread"]), "model_margin": g["model_home_margin"],
                                  "market_margin": -g["home_spread"], "actual_margin": g["home_score"] - g["away_score"],
                                  "verified": g["publication_evidence"] == "independently_verified",
                                  "week": g["week"], "kickoff": g["kickoff"], "recorded": g["forecast_recorded_at"],
                                  "hours": g["hours_before_kickoff"]}
    return [rows[k] for k in sorted(rows)]


def model_vs_market(rows):
    weeks = {}
    for r in rows:
        weeks.setdefault(str(r["week"]), []).append(r)
    by_week = {w: {"games": len(rs), "model_brier": round(statistics.fmean(brier(r["model"], r["y"]) for r in rs), 4),
                   "market_brier": round(statistics.fmean(brier(r["market"], r["y"]) for r in rs), 4)}
               for w, rs in sorted(weeks.items(), key=lambda kv: int(kv[0]))}
    return {
        "forecast_kind": "authentic_pregame",
        "timing": {"median_hours_forecast_before_kickoff": round(statistics.median(r["hours"] for r in rows), 1) if rows else None,
                   "earliest_kickoff": min((r["kickoff"] for r in rows), default=None),
                   "latest_kickoff": max((r["kickoff"] for r in rows), default=None),
                   "note": "The market value is the closing spread, observed at kickoff, after the model forecast was recorded; "
                           "the market therefore had later information (injuries, weather, line moves)."},
        "all_authentic": evaluate([dict(r) for r in rows], "all forecasts recorded before kickoff with a non-disputed closing spread"),
        "independently_verified": evaluate([dict(r) for r in rows if r["verified"]], "independently verified publication cohort"),
        "by_week": by_week,
        "model_total": MODEL_TOTAL,
        "retrospective_replays": "not used: no 2016-2025 model forecasts were archived before kickoff",
    }


# ---------------------------------------------------------------- build / check
def build(lines_dir=LINES_DIR, comparison_dir=COMPARISON_DIR, archive=ARCHIVE, current=CURRENT):
    lines = {}
    for f in sorted(Path(lines_dir).glob("*.json")):
        p = json.loads(f.read_text())
        lines[p["team"]] = p["games"]
    integ, problems = integrity(lines, results_index(archive, current))
    if problems:
        raise ValidationFailed("archive integrity failed: " + "; ".join(problems[:5]))
    rows = comparison_population(comparison_dir)
    result = {
        "schema_version": 1,
        "milestone": "V7 M6 historical validation",
        "frozen_inputs_sha256": {"lines_dir": sha256_dir(lines_dir), "comparison_dir": sha256_dir(comparison_dir),
                                 "verified_results_archive": sha256_file(archive), "current_results": sha256_file(current),
                                 "forecast_ledger": sha256_file(LEDGER), "verified_publication_rows": sha256_file(VERIFIED)},
        "method": {"bootstrap_resamples": BOOTSTRAP, "bootstrap_seed": SEED, "interval": "95% paired percentile bootstrap; Wilson for proportions",
                   "market_probability": "closing spread converted with the existing logistic (scale 19.5)",
                   "outcome": "home team won (no ties in the sample)"},
        "archive_integrity": integ,
        "national_market_checks": national(lines),
        "model_vs_market": model_vs_market(rows),
        "limitations": [
            "Authentic pregame forecasts exist only for 2026 Weeks 10-13; 2016-2025 have no archived model forecasts, so no historical model-vs-market evaluation is possible.",
            "125 games is a small sample; intervals are wide and week-to-week stability cannot be established.",
            "The model's forecasts were recorded days before kickoff; the closing spread reflects later information.",
            "The incumbent model produces no game totals, so totals are evaluated only descriptively (over rate), never model-vs-market.",
            "No result here is evidence of a profitable betting strategy; bookmaker margins are not modelled.",
        ],
    }
    assert_metrics_safe(result)
    return result


def serialize(payload):
    return json.dumps(payload, indent=1, sort_keys=True) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = build()
    text = serialize(result)
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            print(f"{OUTPUT} differs from regeneration", file=sys.stderr)
            return 1
        print("check: byte-identical")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(text)
    tmp.replace(OUTPUT)
    a = result["model_vs_market"]["all_authentic"]
    print(f"integrity rows: {result['archive_integrity']['team_game_rows_checked']}; authentic games: {a['games']}; {a.get('conclusion', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
