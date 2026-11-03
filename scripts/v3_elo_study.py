"""Bounded V3 retrospective Elo sensitivity study.

Research-only: predictions are reconstructed chronologically, NOT archived
pregame forecasts. Tune only on development seasons, evaluate holdout once.
"""
import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import groupby
from math import log
from pathlib import Path

try:
    from scripts.v33_paired_scores import paired_score
except ModuleNotFoundError:
    from v33_paired_scores import paired_score  # direct script execution


def evaluate(games, *, k=24, home_advantage=55, holdout=2025):
    if not 0 < k <= 100 or not 0 <= home_advantage <= 200:
        raise ValueError("Invalid model parameters")
    records = []
    seen = set()
    for original in games:
        g = dict(original)
        kickoff = datetime.fromisoformat(g["kickoff"].replace("Z", "+00:00"))
        if kickoff.tzinfo is None:
            raise ValueError("Timezone-aware kickoff required")
        key = (g["season"], str(g["game_id"]))
        if key in seen:
            raise ValueError(f"Duplicate game: {key}")
        seen.add(key)
        g["_kickoff"] = kickoff
        records.append(g)
    records.sort(key=lambda g: (g["_kickoff"], str(g["game_id"])))
    ratings = defaultdict(lambda: 1500.0)
    pending = []
    predictions = []
    fcs_scored = []
    for kickoff, batch in groupby(records, lambda g: g["_kickoff"]):
        ready = [u for u in pending if u[0] <= kickoff]
        pending = [u for u in pending if u[0] > kickoff]
        for _, home, away, delta in ready:
            ratings[home] += delta
            ratings[away] -= delta
        for g in batch:
            hd, ad = g.get("home_division"), g.get("away_division")
            if hd not in ("FBS", "FCS") or ad not in ("FBS", "FCS"):
                continue
            hs, away_score = g.get("home_score"), g.get("away_score")
            if hs is None or away_score is None or hs == away_score:
                continue
            home, away = g["home"], g["away"]
            advantage = 0 if g.get("neutral_site") else home_advantage
            p = 1 / (1 + 10 ** (-(ratings[home] + advantage - ratings[away]) / 400))
            y = int(hs > away_score)
            row = {"season": g["season"], "game_id": str(g["game_id"]),
                   "home_probability": p, "home_won": y}
            if hd == ad == "FBS":
                predictions.append(row)
            elif "FBS" in (hd, ad) and "FCS" in (hd, ad):
                fcs_scored.append(row)
            pending.append((kickoff + timedelta(hours=4), home, away, k * (y - p)))
    def score(rows):
        if not rows:
            return {"games": 0, "accuracy": None, "brier": None, "logloss": None}
        n = len(rows)
        return {
            "games": n,
            "accuracy": sum((r["home_probability"] >= .5) == bool(r["home_won"]) for r in rows) / n,
            "brier": sum((r["home_probability"] - r["home_won"]) ** 2 for r in rows) / n,
            "logloss": -sum(r["home_won"] * log(max(1e-12, r["home_probability"])) +
                            (1-r["home_won"]) * log(max(1e-12, 1-r["home_probability"]))
                            for r in rows) / n,
        }
    return {
        "predictions": {"fbs_fbs": predictions, "fbs_fcs": fcs_scored},
        "development": score([r for r in predictions if r["season"] < holdout]),
        "holdout": score([r for r in predictions if r["season"] == holdout]),
        "excluded_future_games": sum(r["season"] > holdout for r in predictions),
        "fbs_fcs": {
            "development": score([r for r in fcs_scored if r["season"] < holdout]),
            "holdout": score([r for r in fcs_scored if r["season"] == holdout]),
        },
    }


def study(paths, *, holdout=2025):
    games = [g for path in paths for g in json.loads(Path(path).read_text())]
    if not any(g["season"] < holdout for g in games):
        raise ValueError("No development seasons; cannot select model")
    if not any(g["season"] == holdout for g in games):
        raise ValueError("Holdout season missing")
    # Predeclared small grid; no iterative holdout tuning.
    grid = [(24, 55), (16, 55), (32, 55), (24, 0), (24, 75)]
    candidates = []
    for k, advantage in grid:
        result = evaluate(games, k=k, home_advantage=advantage, holdout=holdout)
        candidates.append({"k": k, "home_advantage": advantage, **result})
    # Primary: development Brier. Tie: prefer incumbent (24,55).
    ranked = sorted(candidates, key=lambda r: (
        r["development"]["brier"] if r["development"]["brier"] is not None else float("inf"),
        (r["k"], r["home_advantage"]) != (24, 55)))
    selected = ranked[0]
    incumbent = candidates[0]
    paired_holdout = {}
    for label in ("fbs_fbs", "fbs_fcs"):
        incumbent_rows = [r for r in incumbent["predictions"][label] if r["season"] == holdout]
        candidate_rows = [r for r in selected["predictions"][label] if r["season"] == holdout]
        paired_holdout[label] = paired_score(incumbent_rows, candidate_rows)
    # Keep existing report schema compact: per-game records are research-only intermediates.
    for candidate in candidates:
        candidate.pop("predictions")
    return {
        "paired_holdout": paired_holdout,
        "type": "v3_retrospective_elo_sensitivity",
        "disclaimer": "Chronologically reconstructed predictions, NOT archived pregame forecasts.",
        "holdout_season": holdout,
        "selection_metric": "development_brier_only",
        "incumbent": incumbent,
        "selected": selected,
        "candidates": candidates,
        "holdout_is_not_used_for_selection": True,
        "promotion_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("games", nargs="+", type=Path)
    parser.add_argument("--holdout", type=int, default=2025)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = study(args.games, holdout=args.holdout)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
