"""Collect reproducible CFBD historical recruiting evaluation inputs.

Retrospective retrieval is not evidence of historical pregame availability.
Only completed seasons explicitly supplied by the operator are included.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from .v34_recruiting_ingestion import normalize_recruiting_classes

BASE = "https://api.collegefootballdata.com"


def fetch_json(path, *, api_key):
    request = Request(BASE + path, headers={"Authorization": "Bearer " + api_key,
                                            "Accept": "application/json"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def collect_snapshot(seasons, *, api_key, fetch=fetch_json):
    if not seasons or len(set(seasons)) != len(seasons) or any(type(y) is not int or y < 2000 for y in seasons):
        raise ValueError("Distinct historical seasons required")
    if not api_key:
        raise ValueError("CFBD_API_KEY required")
    classes, games, members = [], {}, {}
    retrieved = datetime.now(timezone.utc).isoformat()
    for year in sorted(seasons):
        recruiting = fetch(f"/recruiting/teams?year={year}", api_key=api_key)
        season_games = fetch(f"/games?year={year}&seasonType=both", api_key=api_key)
        fbs = fetch(f"/teams/fbs?year={year}", api_key=api_key)
        if not isinstance(recruiting, list) or not recruiting or not isinstance(season_games, list) or not season_games or not isinstance(fbs, list) or not fbs:
            raise ValueError(f"Missing CFBD data for {year}; refusing incomplete snapshot")
        team_names = [team.get("school") for team in fbs]
        if any(not isinstance(name, str) or not name.strip() for name in team_names) or len(set(team_names)) != len(team_names):
            raise ValueError(f"Invalid FBS membership for {year}")
        classes.extend(normalize_recruiting_classes(recruiting, retrieved_at=retrieved))
        games[str(year)] = season_games
        members[str(year)] = sorted(team_names)
    return {"classes": classes, "games_by_season": games,
            "fbs_teams_by_season": members, "completed_seasons": sorted(seasons),
            "retrieved_at": retrieved, "historical_asof_verified": False,
            "source": "CFBD recruiting/teams, games, teams/fbs"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.end < args.start or args.end >= datetime.now(timezone.utc).year:
        parser.error("Choose completed historical seasons only")
    payload = collect_snapshot(list(range(args.start, args.end + 1)),
                               api_key=os.environ.get("CFBD_API_KEY"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
