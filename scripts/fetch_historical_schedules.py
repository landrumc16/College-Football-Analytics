"""Download and audit historical SportsDataverse schedules, 2022-2025.

Requires: pip install pyarrow. Never treats retrospective data as archived forecasts.
"""
import argparse
import json
from pathlib import Path
from urllib.request import urlretrieve

import pyarrow.parquet as pq

URL = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/cfb_schedules/cfb_schedules_{season}.parquet"
COLUMNS = ["game_id", "season", "week", "season_type", "start_date",
           "completed", "home_team", "away_team", "home_division",
           "away_division", "home_points", "away_points", "neutral_site",
           "fbs_game", "fbs_participant"]


def run(output: Path, seasons=range(2022, 2026)):
    output.mkdir(parents=True, exist_ok=True)
    report = {"source": URL, "seasons": {}, "scope": "historical results only; no pregame predictions"}
    for season in seasons:
        path = output / f"cfb_schedules_{season}.parquet"
        if not path.exists():
            urlretrieve(URL.format(season=season), path)
        table = pq.read_table(path, columns=COLUMNS)
        rows = table.to_pylist()
        ids = [str(r["game_id"]) for r in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate game IDs in {season}")
        if any(int(r["season"]) != season for r in rows):
            raise ValueError(f"Wrong season in {season} archive")
        completed = [r for r in rows if r["completed"] is True]
        fbs = [r for r in completed if r["fbs_game"] is True]
        fcs = [r for r in completed if r["fbs_participant"] is True
               and r["fbs_game"] is not True]
        if any(r["home_points"] is None or r["away_points"] is None for r in fbs):
            raise ValueError(f"Missing completed FBS score in {season}")
        report["seasons"][str(season)] = {
            "all_games": len(rows),
            "completed": len(completed),
            "completed_fbs_vs_fbs": len(fbs),
            "completed_fbs_vs_other": len(fcs),
            "missing_fbs_kickoff": sum(not r["start_date"] for r in fbs),
        }
        (output / f"games_{season}.json").write_text(
            json.dumps([{
                "season": season, "game_id": str(r["game_id"]),
                "home": r["home_team"], "away": r["away_team"],
                "home_division": (r["home_division"] or "UNKNOWN").upper(),
                "away_division": (r["away_division"] or "UNKNOWN").upper(),
                "kickoff": r["start_date"],
                "source": URL.format(season=season),
                "home_score": r["home_points"], "away_score": r["away_points"],
                "neutral_site": r["neutral_site"],
                "week": r["week"], "season_type": r["season_type"]
            } for r in completed if r["fbs_participant"] is True],
                       indent=2) + "\n", encoding="utf-8")
    (output / "coverage.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("historical-data"))
    args = parser.parse_args()
    run(args.output)
