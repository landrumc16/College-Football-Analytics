"""Retrospective Elo walk-forward baseline. NOT archived pregame forecasts."""
import argparse
import json
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from math import log
from pathlib import Path


def run(paths, output):
    games = [g for path in paths for g in json.loads(Path(path).read_text())]
    for g in games:
        g["_time"] = datetime.fromisoformat(g["kickoff"].replace("Z", "+00:00"))
        if g["_time"].tzinfo is None:
            raise ValueError("Timezone-aware kickoff required")
    games.sort(key=lambda g: (g["_time"], str(g["game_id"])))
    seen, ratings, predictions = set(), defaultdict(lambda: 1500.0), []
    for kickoff, batch_iter in groupby(games, key=lambda g: g["_time"]):
      updates = []
      for g in batch_iter:
        key = (g["season"], str(g["game_id"]))
          if key in seen:
              raise ValueError(f"Duplicate game: {key}")
          seen.add(key)
          home, away = g["home"], g["away"]
          hd, ad = g.get("home_division"), g.get("away_division")
          if hd not in ("FBS", "FCS") or ad not in ("FBS", "FCS"):
              continue
          hs, ass = g.get("home_score"), g.get("away_score")
          if hs is None or ass is None or hs == ass:
              continue
          advantage = 0 if g.get("neutral_site") else 55
          p = 1 / (1 + 10 ** (-(ratings[home] + advantage - ratings[away]) / 400))
          actual = int(hs > ass)
          if hd == ad == "FBS":
              predictions.append({"season": g["season"], "game_id": str(g["game_id"]),
                                  "home": home, "away": away, "kickoff": g["kickoff"],
                                  "home_probability": p, "home_won": actual})
          delta = 24 * (actual - p)
          updates.append((home, away, delta))
  
      for home, away, delta in updates:
        ratings[home] += delta
        ratings[away] -= delta

    def score(rows):
        n = len(rows)
        if not n:
            return {"games": 0, "accuracy": None, "brier": None, "logloss": None}
        return {"games": n,
                "accuracy": sum((x["home_probability"] >= .5) == bool(x["home_won"]) for x in rows) / n,
                "brier": sum((x["home_probability"] - x["home_won"]) ** 2 for x in rows) / n,
                "logloss": -sum(x["home_won"] * log(max(x["home_probability"], 1e-12)) +
                                (1-x["home_won"]) * log(max(1-x["home_probability"], 1e-12))
                                for x in rows) / n}

    seasons = sorted({g["season"] for g in games})
    report = {"type": "retrospective_walk_forward_baseline",
              "disclaimer": "Not an archived pregame forecast or the original workbook model.",
              "fcs_policy": "FBS-FCS games update ratings but are excluded from accuracy",
              "overall": score(predictions),
              "by_season": {str(y): score([x for x in predictions if x["season"] == y])
                            for y in seasons}}
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "walkforward_report.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "walkforward_predictions.json").write_text(json.dumps(predictions, indent=2) + "\n")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("games", nargs="+")
    ap.add_argument("--output", default="historical-data")
    args = ap.parse_args()
    print(json.dumps(run(args.games, args.output), indent=2))
