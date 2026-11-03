"""Run the existing historical recruiting benchmark from local JSON snapshots.

Input JSON: classes (normalized records), games_by_season (CFBD raw rows),
fbs_teams_by_season (season -> team names), completed_seasons (integers).
This command never fetches or fabricates historical data.
"""
import argparse
import json
from pathlib import Path
from .v34_recruiting_evaluation import evaluate_historical_recruiting


def evaluate_snapshot(payload):
    required = ("classes", "games_by_season", "fbs_teams_by_season", "completed_seasons")
    if not all(key in payload for key in required):
        raise ValueError("Snapshot must include classes, games_by_season, fbs_teams_by_season, completed_seasons")
    years = payload["completed_seasons"]
    if not isinstance(years, list) or any(type(year) is not int for year in years) or len(set(years)) != len(years):
        raise ValueError("Completed seasons must be unique integers")
    return evaluate_historical_recruiting(payload["classes"],
             {int(year): games for year, games in payload["games_by_season"].items()},
             fbs_teams_by_season={int(year): set(teams) for year, teams in payload["fbs_teams_by_season"].items()},
             completed_seasons=set(years))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = evaluate_snapshot(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
