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
        # Read the actual release schema rather than assuming CFBD field names.
        table = pq.read_table(path)
        available = set(table.column_names)
        aliases = {
            "game_id": ("game_id", "id"),
            "season": ("season",),
            "week": ("week",),
            "season_type": ("season_type",),
            "start_date": ("start_date", "startDate"),
            "completed": ("completed",),
            "home_team": ("home_team", "homeTeam"),
            "away_team": ("away_team", "awayTeam"),
            "home_division": ("home_division", "home_classification"),
            "away_division": ("away_division", "away_classification"),
            "home_points": ("home_points", "homePoints"),
            "away_points": ("away_points", "awayPoints"),
            "neutral_site": ("neutral_site", "neutralSite"),
        }
        selected = {name: next((a for a in names if a in available), None)
                    for name, names in aliases.items()}
        required = ("game_id", "season", "week", "start_date", "home_team",
                    "away_team", "home_points", "away_points")
        missing = [name for name in required if selected[name] is None]
        if missing:
            raise ValueError(f"{season}: missing {missing}; actual columns: {sorted(available)}")
        rows = [{name: raw.get(column) if column else None
                 for name, column in selected.items()}
                for raw in table.to_pylist()]
        # Keep the source's authoritative FBS flags where supplied.
        source_flags = [{"fbs_game": raw.get("fbs_game"),
                         "fbs_participant": raw.get("fbs_participant")}
                        for raw in table.select([c for c in ("fbs_game", "fbs_participant")
                                                 if c in available]).to_pylist()]
        for row, flags in zip(rows, source_flags):
            row["home_division"] = str(row["home_division"] or "UNKNOWN").upper()
            row["away_division"] = str(row["away_division"] or "UNKNOWN").upper()
            if row["completed"] is None:
                row["completed"] = (row["home_points"] is not None
                                    and row["away_points"] is not None)
            row["fbs_game"] = (flags["fbs_game"] if flags["fbs_game"] is not None
                               else row["home_division"] == "FBS"
                               and row["away_division"] == "FBS")
            row["fbs_participant"] = (flags["fbs_participant"]
                                      if flags["fbs_participant"] is not None
                                      else "FBS" in (row["home_division"], row["away_division"]))
        if not any(row["fbs_participant"] for row in rows):
            raise ValueError(f"{season}: no FBS classifications; cannot infer from team names")
        report.setdefault("schema_columns", {})[str(season)] = sorted(available)
        ids = [str(r["game_id"]) for r in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate game IDs in {season}")
        if any(int(r["season"]) != season for r in rows):
            raise ValueError(f"Wrong season in {season} archive")
        completed = [r for r in rows if r["completed"] is True and r["home_points"] is not None and r["away_points"] is not None]
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
                "kickoff": str(r["start_date"]),
                "source": URL.format(season=season),
                "home_score": int(r["home_points"]), "away_score": int(r["away_points"]),
                "neutral_site": r["neutral_site"],
                "week": r["week"], "season_type": r["season_type"]
            } for r in completed if r["fbs_participant"] is True and r["start_date"]],
                       indent=2) + "\n", encoding="utf-8")
    (output / "coverage.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("historical-data"))
    args = parser.parse_args()
    run(args.output)
